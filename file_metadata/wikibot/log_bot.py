#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to run analysis on lots of files and show statistics and so on about it.
This tries to add all possible analysis about the file and is a very
developmental and possible messy script.

Syntax:

    wikibot-filemeta-bulk [-arguments ...]

Arguments can be:

-showinfo      Show either "cats", "info" or if left empty defaults to "all".

-limitsize     The maximum file size to download and parse in mega bytes.
               Default is 100MB.
               Example: "-limitsize:10" only analyzes files less than 10MB.

-cachefiles    If used, the files are cached into a folder called "cache" in
               current directory. The directory can be given by using
               "-cachefiles:/place/to/cache". It should already exist.

-dry           If used, the output is printed on the terminal and not to the
               User page.

-skip          If used, all the images in the pagegenerator is not processed.
               After every image it processes, it skips the number of images
               provided as the argument.
               Example: "-skip:1" can be used to only run on alternate images.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import logging
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime

import numpy
from six import string_types
from six.moves.urllib.error import URLError

from file_metadata.generic_file import GenericFile
from file_metadata.utilities import download, retry

try:
    import pywikibot
except ImportError:
    logging.error("To run the script, pywikibot is required. Please install "
                  "it and try again. The nightly version of pywikibot can be "
                  "installed with `pip install git+https://"
                  "gerrit.wikimedia.org/r/pywikibot/core.git#egg=pywikibot`")
    sys.exit(1)
except RuntimeError as err:
    if (len(err.args) > 0 and
            "No user-config.py found in directory" in err.args[0]):
        logging.error("A user-config.py is require to run the pywikibot "
                      "script. To create the user-config.py run the "
                      "command `wikibot-create-config`.")
        sys.exit(1)
from pywikibot import pagegenerators


def stringify(val):
    """
    Convert to val only if it is not already of type string. This is needed
    because strings like \xfa (ú) throw error when str() is used on them
    again.
    """
    return val if isinstance(val, string_types) else str(val)


def make_link(val):
    if val.lower().startswith('category:'):
        return '[[:' + val + ']]'
    elif val.lower().startswith('{{'):
        template = re.sub('(^{{|}}$)', '', val)
        tlx = re.sub('=', '&#61;', template)
        return '{{tlx|' + tlx + '}}'
    else:
        return '[[:' + val + ']]'


def dump_log(data, logname, append=False):
    if isinstance(data, (tuple, list)):
        data = "\n".join(data)
    if not isinstance(data, string_types):
        raise ValueError('Unexpected output got. Expected str, tuple, '
                         'list but got {0}.'.format(type(data)))
    page = pywikibot.Page(
        pywikibot.Site(),
        'User:{user}/logs/{name}'.format(user=pywikibot.Site().username(),
                                         name=logname))
    if append:
        data = page.text + '\n' + data
    if options.get('dry'):
        pywikibot.output(data)
    else:
        page.put(data, "Logged using file-metadata")


@retry(IOError, tries=3)
def download_page(page, timeout=None):
    fname = page.title(as_filename=True).encode('ascii', 'replace')
    fpath = os.path.join(options.get('cachefiles', tempfile.gettempdir()),
                         fname)
    download(page.fileUrl(), fpath, timeout=timeout)
    return fpath


def handle_bulk_pages(gen):
    parsed_pages = set()
    log, categories, category_buckets = [], [], []
    count, exception_count = 0, 0
    total_start_time = datetime.now()
    for ipage, page in enumerate(gen):
        if not (page.exists() and
                not page.isRedirectPage() and
                page.namespace() == "File" and
                page.title() not in parsed_pages and
                (page.latest_file_info['size'] / 1024 / 1024 <
                 options.get('limitsize', float("inf"))) and
                ipage % (options.get('skip', 0) + 1) == 0):
            continue
        parsed_pages.add(page.title())
        try:
            page_path = download_page(page, timeout=15 * 60)
        except URLError:  # Download timed out
            continue

        pywikibot.output(str(count + 1) + '. Analyzing ' +
                         page.title(underscore=False))

        start_time = datetime.now()
        _file = GenericFile.create(page_path)
        try:
            meta = _file.analyze()
        except Exception as err:
            logging.exception(err)
            exception_count += 1
            continue
        finally:
            _file.close()

        info, cats, cat_buckets, img = [], set(), set(), []
        # info - Information analyzed from the file
        # cats - The suggested categories to add to the file
        # im - Image preview with bounding boxes (if applicable)

        #################################################################
        # Mime analysis
        mime = meta.get('File:MIMEType', "ERROR")
        info.append("* '''Mime Type''': " + mime)
        if mime == 'application/ogg':
            _type = meta.get('File:FileType', 'ERROR')
            info.append("* '''File type''': " + _type)

        mime_cats = {
            "JPEG files": {'image/jpeg'},
            "GIF files": {'image/gif'},
            "PNG files": {'image/png'},
            "TIFF files": {'image/tiff'},
            "XCF files": {'image/x-xcf', 'application/x-xcf'},
            "FLAC files": {'audio/x-flac'},
            "WAV files": {'audio/x-wav'},
            "MIDI files": {'audio/midi'},
            "DjVu files": {'image/vnd-djvu', 'image/vnd.djvu'},
            "PDF files": {'application/pdf'},
            "SVG files": {'svg'}
        }
        for cat, mimeset in mime_cats.items():
            if mime in mimeset or meta.get('Composite:FileFormat') in mimeset:
                cats.add('Category:' + cat)
                cat_buckets.add('Type')
                break

        #################################################################
        # Software analysis
        # Find more files at https://commons.wikimedia.org/wiki/
        # Category:Created_with_..._templates
        if (meta.get('SVG:Output_extension', '') ==
                'org.inkscape.output.svg.inkscape'):
            # Example: File:Db-omega.svg , Joetsu_Shinkansen_icon.png
            cats.add('{{Created with Inkscape}}')

        for sw_key in ('PNG:Software', 'EXIF:Software'):
            sw = stringify(meta.get(sw_key, ''))
            if re.match('MATLAB', sw, re.I):
                # Example: File:Fat_absoprtion.png
                cats.add('{{Created with MATLAB}}')
            elif re.match('ImageMagick', sw, re.I):
                # Example: File:Groz-01.PNG
                match = re.match(r'ImageMagick (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with ImageMagick' + ver + '}}')
            elif re.match('Adobe ImageReady', sw, re.I):
                # Example: File:Holtz.png
                cats.add('{{Created with Adobe ImageReady}}')
            elif re.match('Adobe Photoshop', sw, re.I):
                if re.match('Elements', sw, re.I):
                    # Example: File:1010_Bazylika_archikatedralna_%C5%9
                    #               Bw_Jakuba_Szczecin_sygnaturka_0.jpg
                    cats.add('{{Created with Adobe Photoshop Elements}}')
                elif re.match('Express', sw, re.I):
                    # Example: File:Politecnico_di_Milano_Bovisa_4.jpg
                    cats.add('{{Created with Adobe Photoshop Express}}')
                elif re.match(r'Photoshop CS\d?', sw, re.I):
                    match = re.match(r'Photoshop CS\d?', sw, re.I)
                    if match:
                        # Example: File:Cervicomanubriotomie.jpg
                        cats.add('{{Created with Adobe ' +
                                 match.group().strip() + '}}')
                else:
                    # Example: File:Cervicomanubriotomie.jpg
                    cats.add('{{Created with Adobe Photoshop}}')
                # Check if photomerge was used
                if (stringify(meta.get('Photoshop:HasRealMergedData',
                                       '')).lower()
                        in ('1', 'yes')):
                    # Example:01-118_Koenigstein_Panorama.jpg
                    cats.add('{{Created with Photoshop Photomerge}}')
                    cats.add('Category:Panoramics')
            elif re.match('Picasa', sw, re.I):
                # Example: File:08_Ny_Alesund_prn.JPG
                match = re.match(r'Picasa (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with Picasa' + ver + '}}')
            elif re.match('GIMP', sw, re.I):
                # Example: File:2013-04-25_21-09-18-ecl-lune-mosaic.jpg
                match = re.match(r'GIMP (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with GIMP' + ver + '}}')
            elif re.match('Microsoft ICE', sw, re.I):
                # Example: File:Bochnia_kopalnia_kaplica_2.jpg
                match = re.match(r'ICE v(?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with Microsoft Image Composite '
                         'Editor' + ver + '}}')
            elif re.match(r'Paint\.NET', sw, re.I):
                # Example: File:
                match = re.match(r'Paint\.NET v(?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with Paint.NET' + ver + '}}')
            elif re.match('gnome-screenshot', sw, re.I):
                # Example: File:LibreOfficePresentationTeluguExample1.png
                cats.add('Category:Screenshots')
                cat_buckets.add('Content')

        for desc_key in ('SVG:Desc',):
            desc = stringify(meta.get(desc_key, '')).lower()
            if re.match('GNUPLOT', desc, re.I):
                # Example: File:Beta_versus_rapidity.svg
                match = re.match(r'GNUPLOT (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with GNU Plot' + ver + '}}')
            elif re.match('Chemtool', desc, re.I):
                # Example: File:Chitobiose_glucosamine.svg
                match = re.match(r'Chemtool (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with Chemtool' + ver + '}}')
                cats.add('Category:Chemical compounds')
                cats.add('Category:Graphics')
                cat_buckets.add('Content')
            elif re.match('VectorFieldPlot', desc, re.I):
                # Example: File:VFPt_minus.svg
                match = re.match(r'VectorFieldPlot (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with VectorFieldPlot' + ver + '}}')
                cats.add('Category:Field diagrams')
                cats.add('Category:Graphics')
                cat_buckets.add('Content')

        for comment_key in ('PNG:Comment', 'File:Comment'):
            comment = stringify(meta.get(comment_key, '')).lower()
            if re.match('Stella4D', comment, re.I):
                # Example: File:10-3_deltohedron.png
                match = re.match(r'Stella4D (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with Stella' + ver + '}}')
            elif re.match('GIMP', comment, re.I):
                # Example: File:105_H_61-37.jpeg
                cats.add('{{Created with GIMP}}')

        for prod_key in ('PDF:Producer',):
            prod = stringify(meta.get(prod_key, ''))
            if re.match(r'Libre ?Office', prod, re.I):
                match = re.match(r'Libre ?Office (?P<ver>[\d\.]+)', prod, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                if meta.get('PDF:Creator'):
                    cats.add('{{Created with LibreOffice ' +
                             meta['PDF:Creator'] + ver + '}}')
                else:
                    cats.add('{{Created with LibreOffice' + ver + '}}')
            elif re.match(r'doPDF', prod, re.I):
                cats.add('{{Created with doPDF}}')
            elif re.match(r'ACDSee', prod, re.I):
                cats.add('{{Created with ACDSee}}')
            elif re.match(r'iText', prod, re.I):
                cats.add('{{Created with iText}}')

        #################################################################
        # Device analysis
        model = stringify(meta.get('EXIF:Model', ''))
        make = stringify(meta.get('EXIF:Make', ''))
        if model:
            # Modify the model so that it conforms to the category names
            for _make in ('NIKON', 'FUJIFILM', 'Xiaomi', 'Panasonic', 'SONY',
                          'Nokia'):
                if make == _make and not re.match(_make, model, re.I):
                    # Category is named as make + model
                    model = make + ' ' + model
            if make == 'i2S DigiBook Scanner':
                model = 'i2s Digibook ' + model
            # Simple replacements
            model = model.replace('NIKON', 'Nikon')
            model = model.replace('PENTAX', 'Pentax')
            model = model.replace('FUJIFILM', 'Fujifilm')
            model = model.replace('SONY', 'Sony')
            if 'nikon' in make.lower():
                model = model.replace('COOLPIX', 'Coolpix')
            if 'xiaomi' in make.lower():
                model = model.replace('Note3', 'Note 3')
            if 'samsung' in make.lower():
                # In samsung, the cameras have multiple names like:
                # "<Digimax S600 / Kenox S600 / Digimax Cyber 630>" or
                # "Digimax A4/Kenox D4". The categories are only named as
                # "Taken with Samsung S600", "Taken with Samsung A4" though.
                samsung_model = ''
                possible_models = re.sub('[<>]', '', model).split('/')
                for imod in possible_models:
                    imod = imod.strip()
                    if (imod.lower().startswith('digimax') and
                            not imod.lower().startswith('digimax cyber')):
                        samsung_model = imod
                        break
                if not samsung_model and len(possible_models) > 0:
                    samsung_model = possible_models[0].strip()
                # Remove digimax if present
                samsung_model = re.sub('Digimax', '', samsung_model, count=1,
                                       flags=re.IGNORECASE).strip()

                model = 'Samsung ' + samsung_model
            if 'olympus' in make.lower():
                model = 'Olympus ' + model
            if 'motorola' in make.lower():
                model = model.replace('MotoG2', 'Moto G2')
                model = model.replace('MotoG3', 'Moto G3')
                model = model.replace('MotoG4', 'Moto G4')
            if 'sanyo' in make.lower():
                model = 'Sanyo ' + model
            if 'canon' in make.lower():
                model = model.replace('EOS REBEL', 'EOS')
            if 'casio' in make.lower():
                model = 'Casio ' + model

            for prefix in ['Sanned with ', 'Taken with ',
                           'Taken or Scanned with ']:
                possible_cat = pywikibot.Page(pywikibot.Site(),
                                              "Category:" + prefix + model)
                if (possible_cat.exists() or
                        prefix == 'Taken or Scanned with '):
                    info.append("* '''Model''': " +
                                possible_cat.title(underscore=False,
                                                   textlink=True, asLink=True))
                    cats.add(possible_cat.title(underscore=False))
                    break

        #################################################################
        # Color analysis
        for key in ['AverageRGB', 'ClosestLabeledColor', 'EdgeRatio',
                    'NumberOfGreyShades', 'PercentFrequentColors',
                    'MeanSquareErrorFromGrey', 'Monochrome', 'UsesAlpha',
                    'IT8TopBar', 'IT8BottomBar', 'IT8TopBarGreyMSE',
                    'IT8BottomBarGreyMSE']:
            if 'Color:' + key in meta:
                if isinstance(meta['Color:' + key], (list, tuple)):
                    val = ', '.join(map(str, meta['Color:' + key]))
                elif isinstance(meta['Color:' + key], float):
                    val = str(round(meta['Color:' + key], 5))
                else:
                    val = stringify(meta['Color:' + key])
                info.append("* '''" + key + "''': " + val)
        greys = meta.get('Color:NumberOfGreyShades')
        edges = meta.get('Color:EdgeRatio')
        if ((greys is not None and greys < 2) or
                (edges is not None and edges < 0.13) or
                meta.get('Composite:FileFormat') == 'svg'):
            cats.add('Category:Graphics')
        if (meta.get('Color:MeanSquareErrorFromGrey', 999) < 22 and
                meta.get('EXIF:Make') is not None):
            # If it's scanned or from a camera and black-white
            cats.add('Category:Black and white photographs')
        if meta.get('Color:UsesAlpha') is True:
            cats.add('Category:Transparent background')

        for spike, greymse in [('Color:IT8TopBar',
                                'Color:IT8TopBarGreyMSE'),
                               ('Color:IT8BottomBar',
                                'Color:IT8BottomBarGreyMSE')]:
            if (18 <= meta.get(spike, -1) <= 22 and
                    meta.get(greymse, 999) < 15):
                cats.add('Category:Scans with IT8 target')
                break

        if meta.get('Misc:StereoCardMSE'):
            info.append("* '''Stereo Card MSE''': " +
                        str(meta.get('Misc:StereoCardMSE')))
        if meta.get('Misc:StereoCardHistogramMSE'):
            info.append("* '''Stereo Card Histogram MSE''': " +
                        str(meta.get('Misc:StereoCardHistogramMSE')))

        #################################################################
        # Location analysis
        for key in ['GPSCity', 'GPSState', 'GPSCountry']:
            val = meta.get('Composite:' + key)
            if val is not None:
                info.append("* '''" + key + "''': " + val)
        for val in [(meta.get('Composite:GPSCity', '') + ', ' +
                     meta.get('Composite:GPSState', '')),
                    (meta.get('Composite:GPSCity', '') + ', ' +
                     meta.get('Composite:GPSCountry', '')),
                    meta.get('Composite:GPSCity', ''),
                    (meta.get('Composite:GPSState', '') + ', ' +
                     meta.get('Composite:GPSCountry', '')),
                    meta.get('Composite:GPSState', ''),
                    meta.get('Composite:GPSCountry', '')]:
            if val:
                if pywikibot.Page(
                        pywikibot.Site(), "Category:" + val).exists():
                    cats.add('Category:' + val)
                    break

        if (meta.get('Composite:GPSLatitude') and
                meta.get('Composite:GPSLongitude')):
            cats.add('{{GPS EXIF}}')
            cat_buckets.add('Location')
            info.append("* '''GPS Coordinates''': {0}, {1}"
                        .format(meta.get('Composite:GPSLatitude'),
                                meta.get('Composite:GPSLongitude')))

        #################################################################
        # Author analysis
        if meta.get('EXIF:Artist') == "New York Public Library":
            cats.add('Category:Images from the New York Public Library')

        #################################################################
        # Image analysis
        # Fill second column (image cell) for ImageFiles (Only 2 dim images)
        if (isinstance(_file.fetch('ndarray'), numpy.ndarray) and
                _file.fetch('ndarray').ndim in (2, 3)):
            height, width = _file.fetch('ndarray').shape[:2]
            max_dim = max(width, height)
            scale = min(200, max_dim) / max_dim

            img.append('<div style="position:relative;">')
            img.append('{0}|{1}x{2}px]]'.format(
                       page.title(underscore=False, asLink=True)[:-2],
                       int(width * scale), int(height * scale)))

            img_bbox = ('<div class="position-marker file-meta-{css_class}" '
                        'style="position:absolute; left:{left}px; '
                        'top:{top}px; width:{width}px; height:{height}px; '
                        'border:2px solid #{color};"></div>')

            def _str_bbox(bbox):
                return ("Left:" + str(bbox['left']) +
                        ", Top:" + str(bbox['top']) +
                        ", Width:" + str(bbox['width']) +
                        ", Height:" + str(bbox['height']))

            def _mean_bbox(bbox):
                return (bbox['left'] + bbox['width'] / 2,
                        bbox['top'] + bbox['height'] / 2)

            def _area_bbox(bbox):
                return bbox['width'] * bbox['height']

            #################################################################
            # Analysis for very specific images: Icons, Football kits, etc
            if height == width and height in (16, 32, 48, 96):
                cats.add('Category:Icons')
            elif width == 100 and height == 36:
                cats.add('Category:Football kit shorts')
                cat_buckets.add('Content')
            elif width == 100 and height == 25:
                cats.add('Category:Football kit socks')
                cat_buckets.add('Content')
            elif width == 38 and height == 59:
                cats.add('Category:Football kit body')
                cat_buckets.add('Content')
            elif width == 31 and height == 59:
                cats.add('Category:Football kit sleeves')
                cat_buckets.add('Content')

            #################################################################
            # Barcode analysis
            bar_cats = {
                "Code 39": ('code_39', 'code39'),
                "Code 93": ('code_93', 'code93'),
                "Code 128": ('code_128', 'code128'),
                "Data Matrix": ('data_matrix',),
                "Quick Response Codes": ('qr_code', 'qrcode')}

            def print_barcode_data(bar):
                info.append("** Data: " + bar['data'])
                info.append("** Format: " + str(bar['format']))
                info.append("** Position : " + _str_bbox(bar['bounding box']))
                box_kwargs = {k: int(v * scale)
                              for k, v in bar['bounding box'].items()}
                box_kwargs["color"] = "ff0000"
                box_kwargs["css_class"] = "barcode"
                img.append(img_bbox.format(**box_kwargs))
                if (bar['bounding box']['height'] < 5 and
                        bar['bounding box']['width'] < 5):
                    return set()
                for cat, formats in bar_cats.items():
                    if bar['format'].lower() in formats:
                        return {'Category:' + cat, 'Category:Barcode'}
                return {'Category:Barcode'}

            # Barcodes from zxing:
            for i, bar in enumerate(meta.get('zxing:Barcodes', [])):
                info.append("* '''Barcode''' (zxing) #" + str(i))
                barcode_cats = print_barcode_data(bar)
                cats = cats.union(barcode_cats)
                if len(barcode_cats) > 0:
                    cat_buckets.add('Content')

            # Barcodes from zbar:
            for i, bar in enumerate(meta.get('zbar:Barcodes', [])):
                info.append("* '''Barcode''' (zbar) #" + str(i))
                barcode_cats = print_barcode_data(bar)
                cats = cats.union(barcode_cats)
                if len(barcode_cats) > 0:
                    cat_buckets.add('Content')

            #################################################################
            # Face analysis
            def print_face_data(face, _type):
                _cats = set()  # These may or may not be added ...
                feats = set()
                _cats.add('Category:Human faces')
                _cats.add('Category:Unidentified people')
                if _type == 'opencv':  # Dlib always finds all features
                    if len(face.get('eyes', ())) > 0:
                        # _cats.add('Category:Human eyes')
                        feats.add('Eyes (' + str(len(face['eyes'])) + ')')
                    if face.get('ears') is not None:
                        # _cats.add('Category:Human ears')
                        feats.add('Ears')
                    if face.get('nose') is not None:
                        # _cats.add('Category:Human noses')
                        feats.add('Nose')
                    if face.get('mouth') is not None:
                        # _cats.add('Category:Human mouths')
                        feats.add('Mouth')
                    if face.get('glasses') is not None:
                        _cats.add('Category:People with glasses')
                        feats.add('Glasses')

                if (face['position']['height'] * face['position']['width'] >
                        0.55 * height * width):
                    # If face is very large...
                    _cats.add('Category:Portrait')

                if _type == 'dlib':
                    info.append("** Score: " + str(round(face['score'], 3)))
                info.append("** Bounding Box: " + _str_bbox(face['position']))
                if len(feats) > 0:
                    info.append("** Other features: " + ", ".join(feats))
                box_kwargs = {k: int(v * scale)
                              for k, v in face['position'].items()}
                box_kwargs["color"] = "ff0000"
                box_kwargs["css_class"] = "barcode"
                img.append(img_bbox.format(**box_kwargs))
                if ((_type == 'opencv' and len(feats) > 2) or
                        (_type == 'dlib' and face['score'] > 0.045)):
                    return _cats
                return set()

            # Save all face categories in this set, ad add it later if it
            # seems appropirate. This is because we need to delay the writing
            # of these categories based on some logic.
            valid_faces = []
            face_cats = set()

            # Faces with dlib:
            for iface, face in enumerate(meta.get('dlib:Faces', [])):
                info.append("* '''Face''' (dlib) #" + str(iface + 1))
                icats = print_face_data(face, 'dlib')
                face_cats = face_cats.union(icats)
                if 'Category:Human faces' in icats:
                    valid_faces.append(face)

            # Faces with opencv's haarcascades:
            for iface, face in enumerate(meta.get('OpenCV:Faces', [])):
                info.append("* '''Face''' (haarcascade) #" + str(iface + 1))
                icats = print_face_data(face, 'opencv')
                face_cats = face_cats.union(icats)
                if 'Category:Human faces' in icats:
                    valid_faces.append(face)

            if len(valid_faces) >= 3:
                face_cats.add('Category:Groups of people')

            if len(face_cats) > 0:
                cat_buckets.add('Content')
            cats = cats.union(face_cats)
            img.append('</div>')  # Close the image's div

        #################################################################
        # Leaf cats using Location analysis
        if 'Category:Unidentified people' in cats:
            for key in ['GPSState', 'GPSCountry']:
                val = meta.get('Composite:' + key)
                if val is None:
                    continue
                cat_val = "Category:Unidentified people in " + val
                if (pywikibot.Page(pywikibot.Site(), cat_val).exists() or
                        key == 'GPSCountry'):
                    cats.add(cat_val)
                    cats.remove('Category:Unidentified people')
                    break

        if 'Category:Groups of people' in cats:
            for key in ['GPSState', 'GPSCountry']:
                val = meta.get('Composite:' + key)
                if val is None:
                    continue
                cat_val = "Category:Groups of people in " + val
                if (pywikibot.Page(pywikibot.Site(), cat_val).exists() or
                        key == 'GPSCountry'):
                    cats.add(cat_val)
                    cats.remove('Category:Groups of people')
                    break

        categories.append(cats)
        category_buckets.append(cat_buckets)

        info.append("* '''Time taken''': {0} sec"
                    .format((datetime.now() - start_time).total_seconds()))

        count += 1
        log.append("\n==== {0} ====" .format(page.title(asLink=True,
                                                        textlink=True)))
        # Make a table for text and image

        log += ['{| class="wikitable"', '|']
        if options.get('showinfo', "all") in ('all', 'info'):
            log += info
        if options.get('showinfo', "all") in ('all', 'cats'):
            log.append("* '''Categories''' ({0}): {1}"
                       .format(len(cats),
                               ", ".join(make_link(c) for c in cats)))
        log += ['|'] + img + ['|}']
        # Clean up the downloaded file if no need to cache
        if options.get('cachefiles') is None:
            os.remove(page_path)

    if count + exception_count == 0:
        # Nothing happened, don't go on.
        pywikibot.output('Analysis was not run on any files.')
        return

    stats = ["* '''Time taken''': {0} sec"
             .format((datetime.now() - total_start_time).total_seconds())]
    stats += ["* '''Number of files successfully analyzed''': "
              "{0} ({1:0.4f} %)".format(
                  count, 100 * count / (count + exception_count))]
    stats += ["* '''Number of files with exceptions''': "
              "{0} ({1:0.4f} %)".format(
                  exception_count,
                  100 * exception_count / (count + exception_count))]
    cat_counter = Counter(cat for fcats in categories for cat in fcats)
    stats += ["* '''Number of distinct categories used''': {0}"
              .format(len(cat_counter))]

    stats += ['{| class="wikitable sortable plainrowheaders"',
              '|+ Data of files categorized by category name',
              '! Category name',
              '! Number of files',
              '! colspan=2 | Percent of files in the category',
              ]
    for icat, (catname, numfiles) in enumerate(
            sorted(cat_counter.items(), key=lambda x: x[1], reverse=True)):
        stats.append('|-')
        stats.append('! scope=row | ' + make_link(catname))
        stats.append('| ' + str(numfiles))
        stats.append('| {{bartable| ' +
                     str(round(100 * numfiles / count, 2)) + '}}')
    stats.append('|}')

    stats += ['{{User:AbdealiJK/Templates/Bar chart',
              '| title = Histogram of number of categories found per file',
              '| label_type = Number of categories found',
              '| data_type = Number of files with that many categories',
              '| data_max = ' + str(count)]
    for icat, (numcats, numfiles) in \
            enumerate(Counter(len(cats) for cats in categories).items()):
        stats += ['| label{0} = {1} ({2:.4f} %)'.format(
                  icat + 1, numcats, 100 * numfiles / count),
                  '| data{0} = {1}'.format(icat + 1, numfiles)]
    stats.append('}}')

    stats += ['{{User:AbdealiJK/Templates/Bar chart',
              '| title = Histogram of number of categories found per file '
              '(without file-type categories)',
              '| label_type = Number of categories found',
              '| data_type = Number of files with that many categories',
              '| data_max = ' + str(count)]
    file_type_cats = set('Category:' + c for c in mime_cats.keys())
    non_file_type_counter = Counter(
        len(cats - file_type_cats) for cats in categories)
    for icat, (numcats, numfiles) in enumerate(non_file_type_counter.items()):
        stats += ['| label{0} = {1} ({2:.4f} %)'.format(
                  icat + 1, numcats, 100 * numfiles / count),
                  '| data{0} = {1}'.format(icat + 1, numfiles)]
    stats.append('}}')

    stats += ['{{User:AbdealiJK/Templates/Bar chart',
              '| title = Histogram of buckets',
              '| label_type = Bucket name',
              '| data_type = Number of files in bucket',
              '| data_max = ' + str(count)]
    bucket_counter = Counter(
        b for fbuckets in category_buckets for b in fbuckets)
    for ibucket, (bucketname, numfiles) in enumerate(
            sorted(bucket_counter.items(), key=lambda x: x[1], reverse=True)):
        stats += ['| label{0} = {1} ({2:.4f} %)'.format(
                  ibucket + 1, bucketname, 100 * numfiles / count),
                  '| data{0} = {1}'.format(ibucket + 1, numfiles)]
    stats.append('}}')

    log = stats + ['\n'] + log

    # Dump all logs to the log page
    dump_log(log, logname=options.get('logname'))


options = {}


def main(*args):
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for local_arg in local_args:
        if gen_factory.handleArg(local_arg):
            continue
        arg, sep, value = local_arg.partition(':')
        if arg == '-showinfo':
            options[arg[1:]] = value or "all"
            if value not in ("cats", "info", "all"):
                pywikibot.error("Invalid value for -showinfo. It can only be "
                                "cats, info, or all.\nUse -help for further "
                                "information.")
                sys.exit(1)
        elif arg == '-limitsize':
            options[arg[1:]] = int(value) if value != "" else 100
        elif arg == '-cachefiles':
            options[arg[1:]] = value or 'cache'
        elif arg == '-logname':
            options[arg[1:]] = value
        elif arg == '-dry':
            options[arg[1:]] = True
        elif arg == '-skip':
            options[arg[1:]] = int(value) or 0

    if not options.get('dry') and not options.get('logname'):
        pywikibot.error('-logname is required to decide the page to write '
                        'to.\nUse -help for further information.')
        sys.exit(2)

    gen = gen_factory.getCombinedGenerator()
    if not gen:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False
    else:
        pywikibot.Site().login()
        pregenerator = pagegenerators.PreloadingGenerator(gen)
        handle_bulk_pages(pregenerator)
        return True


if __name__ == "__main__":
    main()

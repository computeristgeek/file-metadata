#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to run analysis on files and request the user to accept categories
or not.

Syntax:

    wikibot-filemeta-manual [-arguments ...]

Arguments can be:

-limitsize     The maximum file size to download and parse in mega bytes.
               Default is 100MB.
               Example: "-limitsize:10" only analyzes files less than 10MB.

-cachefiles    If used, the files are cached into a folder called "cache" in
               current directory. The directory can be given by using
               "-cachefiles:/place/to/cache". It should already exist.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import logging
import os
import re
import tempfile

import numpy
from six.moves.urllib.error import URLError

from file_metadata.generic_file import GenericFile
from file_metadata.wikibot.utilities import (pywikibot, download_page,
                                             put_cats, stringify)


def handle_bulk_pages(gen):
    parsed_pages = set()
    count, exception_count = 0, 0

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
        "SVG files": {'svg'},
        "Ogg sound files": {'ogg'},
        "Ogv videos": {'ogv'},
        'WebM videos': {'video/webm'},
    }
    for ipage, page in enumerate(gen):
        if not (page.exists() and
                not page.isRedirectPage() and
                page.namespace() == "File" and
                page.title() not in parsed_pages and
                (page.latest_file_info['size'] / 1024 / 1024 <
                 options.get('limitsize', float("inf")))):
            continue
        parsed_pages.add(page.title())
        try:
            page_path = download_page(
                page, timeout=15 * 60,
                cache_dir=options.get('cachefiles', tempfile.gettempdir()))
        except URLError:  # Download timed out
            continue

        pywikibot.output(str(count + 1) + '. Analyzing ' +
                         page.title(underscore=False))

        _file = GenericFile.create(page_path)
        try:
            meta = _file.analyze()
        except Exception as err:
            logging.exception(err)
            exception_count += 1
            continue
        finally:
            _file.close()

        # cats - The suggested categories to add to the file
        cats = set()

        #################################################################
        # Mime analysis
        mime = meta.get('File:MIMEType', "ERROR")
        for cat, mimeset in mime_cats.items():
            if mime in mimeset or meta.get('Composite:FileFormat') in mimeset:
                cats.add('Category:' + cat)
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
            elif re.match('VectorFieldPlot', desc, re.I):
                # Example: File:VFPt_minus.svg
                match = re.match(r'VectorFieldPlot (?P<ver>[\d\.]+)', sw, re.I)
                ver = '|version=' + match.groupdict()['ver'] if match else ''
                cats.add('{{Created with VectorFieldPlot' + ver + '}}')
                cats.add('Category:Field diagrams')
                cats.add('Category:Graphics')

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
                    cats.add(possible_cat.title(underscore=False))
                    break

        #################################################################
        # Color analysis
        greys = meta.get('Color:NumberOfGreyShades')
        edges = meta.get('Color:EdgeRatio')
        if ((greys is not None and greys < 2) or
                (edges is not None and edges < 0.13) or
                meta.get('Composite:FileFormat') == 'svg'):
            cats.add('Category:Graphics')
        if (meta.get('Color:MeanSquareErrorFromGrey', 999) < 30 and
                meta.get('EXIF:Make') is not None):
            # If it's scanned or from a camera and black-white
            cats.add('Category:Black and white photographs')
        if meta.get('Color:UsesAlpha') is True:
            cats.add('Category:Transparent background')

        #################################################################
        # Location analysis
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

            #################################################################
            # Analysis for very specific images: Icons, Football kits, etc
            if height == width and height in (16, 32, 48, 96):
                cats.add('Category:Icons')
            elif width == 100 and height == 36:
                cats.add('Category:Football kit shorts')
            elif width == 100 and height == 25:
                cats.add('Category:Football kit socks')
            elif width == 38 and height == 59:
                cats.add('Category:Football kit body')
            elif width == 31 and height == 59:
                cats.add('Category:Football kit sleeves')

            #################################################################
            # Barcode analysis
            bar_cats = {
                "Code 39": ('code_39', 'code39'),
                "Code 93": ('code_93', 'code93'),
                "Code 128": ('code_128', 'code128'),
                "Data Matrix": ('data_matrix',),
                "Quick Response Codes": ('qr_code', 'qrcode')}

            def print_barcode_data(bar):
                if (bar['bounding box']['height'] < 3 and
                        bar['bounding box']['width'] < 3):
                    return set()
                for cat, formats in bar_cats.items():
                    if bar['format'].lower() in formats:
                        return {'Category:' + cat, 'Category:Barcode'}
                return {'Category:Barcode'}

            # Barcodes from zxing:
            for i, bar in enumerate(meta.get('zxing:Barcodes', [])):
                barcode_cats = print_barcode_data(bar)
                cats = cats.union(barcode_cats)

            # Barcodes from zbar:
            for i, bar in enumerate(meta.get('zbar:Barcodes', [])):
                barcode_cats = print_barcode_data(bar)
                cats = cats.union(barcode_cats)

            #################################################################
            # Face analysis
            def print_face_data(face, _type):
                _cats = set()  # These may or may not be added ...
                feats = set()
                _cats.add('Category:Human faces')
                _cats.add('Category:Unidentified people')
                if _type == 'opencv':  # Dlib always finds all features
                    if len(face.get('eyes', ())) > 0:
                        feats.add('Eyes (' + str(len(face['eyes'])) + ')')
                    if face.get('ears') is not None:
                        feats.add('Ears')
                    if face.get('nose') is not None:
                        feats.add('Nose')
                    if face.get('mouth') is not None:
                        feats.add('Mouth')
                    if face.get('glasses') is not None:
                        _cats.add('Category:People with glasses')
                        feats.add('Glasses')

                if (face['position']['height'] * face['position']['width'] >
                        0.55 * height * width):
                    # If face is very large...
                    _cats.add('Category:Portrait')

                if ((_type == 'opencv' and len(feats) > 3) or
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
                icats = print_face_data(face, 'dlib')
                face_cats = face_cats.union(icats)
                if 'Category:Human faces' in icats:
                    valid_faces.append(face)

            # Faces with opencv's haarcascades:
            for iface, face in enumerate(meta.get('OpenCV:Faces', [])):
                icats = print_face_data(face, 'opencv')
                face_cats = face_cats.union(icats)
                if 'Category:Human faces' in icats:
                    valid_faces.append(face)

            if len(valid_faces) >= 3:
                face_cats.add('Category:Groups of people')

            cats = cats.union(face_cats)

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

        count += 1

        # Write the categories to the page
        put_cats(page, cats)

        # Clean up the downloaded file if no need to cache
        if options.get('cachefiles') is None:
            os.remove(page_path)

    if count + exception_count == 0:  # Nothing happened, don't go on.
        pywikibot.output('Analysis was not run on any files.')
        return

options = {}


def main(*args):
    local_args = pywikibot.handle_args(args)
    gen_factory = pywikibot.pagegenerators.GeneratorFactory()

    for local_arg in local_args:
        if gen_factory.handleArg(local_arg):
            continue
        arg, sep, value = local_arg.partition(':')
        if arg == '-limitsize':
            options[arg[1:]] = int(value) if value != "" else 100
        elif arg == '-cachefiles':
            options[arg[1:]] = value or 'cache'

    gen = gen_factory.getCombinedGenerator()
    if not gen:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False
    else:
        pywikibot.Site().login()
        pregenerator = pywikibot.pagegenerators.PreloadingGenerator(gen)
        handle_bulk_pages(pregenerator)
        return True


if __name__ == "__main__":
    main()

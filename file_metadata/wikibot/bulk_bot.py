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
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import logging
import os
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
except RuntimeError as err:
    if (len(err.args) > 1 and
            "No user-config.py found in director" in err.args[0]):
        print("A user-config.py is require to run the pywikibot script. To"
              "create the user-config.py run the command "
              "`wikibot-create-config`.")
from pywikibot import pagegenerators


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
    log, categories = [], []
    count, exception_count = 0, 0
    total_start_time = datetime.now()
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
            page_path = download_page(page, timeout=15 * 60)
        except URLError:  # Download timed out
            continue

        print(count + 1, '. Analyzing', page.title(underscore=False))

        start_time = datetime.now()
        try:
            _file = GenericFile.create(page_path)
            meta = _file.analyze()
        except Exception as err:
            logging.exception(err)
            exception_count += 1
            continue
        finally:
            _file.close()

        info, cats, img = [], set(), []
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
                break

        #################################################################
        # Software analysis
        softwares = meta.get('Composite:Softwares', [])
        software_cats = {
            'Microsoft ICE': 'Microsoft Image Composite Editor',
            'GNU Plot': 'Gnuplot'
        }
        if len(softwares) > 0:
            for sw in softwares:
                info.append("* '''Softwares''': " + ", ".join(softwares))
                cats.add('Category:Created with ' + software_cats.get(sw, sw))

        # Screenshot:
        screenshot_softwares = meta.get('Composite:ScreenshotSoftwares', [])
        if len(screenshot_softwares) > 0:
            info.append('* Category:Screenshots')
            for sw in screenshot_softwares:
                info.append("* '''Screenshot Softwares''': " +
                            ", ".join(screenshot_softwares))

        #################################################################
        # Device analysis
        model = meta.get('EXIF:Model', '')
        make = meta.get('EXIF:Make', '')
        if model:
            # Modify the model so that it conforms to the category names
            if make in ('FUJIFILM', 'Xiaomi'):
                # Category is named as make + model
                model = make + model
            elif make == 'i2S DigiBook Scanner':
                model = 'i2s Digibook ' + model
            # Simple replacements
            model.replace('NIKON', 'Nikon')
            model.replace('FUJIFILM', 'Nikon')
            if make.lower() == 'xiaomi':
                model.replace('Note3', 'Note 3')  # Some pics have "Note3"

            possible_prefixes = ['Sanned with ', 'Taken with ',
                                 'Taken or Scanned with ']
            for prefix in possible_prefixes:
                possible_cat = pywikibot.Page(pywikibot.Site(),
                                              "Category:" + prefix + model)
                if possible_cat.exists():
                    info.append("* '''Model''': " +
                                possible_cat.title(underscore=False,
                                                   textlink=True, asLink=True))
                    cats.add(possible_cat.title(underscore=False))

        #################################################################
        # Color analysis
        for key in ['AverageRGB', 'ClosestLabeledColor', 'EdgeRatio',
                    'NumberOfGreyShades', 'PercentFrequentColors']:
            if 'Color:' + key in meta:
                if isinstance(meta['Color:' + key], (list, tuple)):
                    val = ', '.join(map(str, meta['Color:' + key]))
                elif isinstance(meta['Color:' + key], float):
                    val = str(round(meta['Color:' + key], 5))
                else:
                    val = str(meta['Color:' + key])
                info.append("* '''" + key + "''': " + val)
        greys = meta.get('Color:NumberOfGreyShades')
        edges = meta.get('Color:EdgeRatio')
        if ((greys is not None and greys < 2) or
                (edges is not None and edges < 0.13)):
            cats.add('Category:Graphics')

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

            #################################################################
            # Icon analysis
            if height == width and height in (16, 32, 48, 96):
                cats.add('Category:Icons')

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
                cats = cats.union(print_barcode_data(bar))

            # Barcodes from zbar:
            for i, bar in enumerate(meta.get('zbar:Barcodes', [])):
                info.append("* '''Barcode''' (zbar) #" + str(i))
                cats = cats.union(print_barcode_data(bar))

            #################################################################
            # Face analysis
            def print_face_data(face):
                _cats = set()  # These may or may not be added ...
                feats = set()
                _cats.add('Category:Human faces')
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

                info.append("** Bounding Box: " + _str_bbox(face['position']))
                if len(feats) > 0:
                    info.append("** Other features: " + ", ".join(feats))
                box_kwargs = {k: int(v * scale)
                              for k, v in face['position'].items()}
                box_kwargs["color"] = "ff0000"
                box_kwargs["css_class"] = "barcode"
                img.append(img_bbox.format(**box_kwargs))
                if len(feats) > 2:
                    # Atleast 1 feature is needed to reliably detect it as
                    # a face
                    return _cats
                return set()

            # Faces with dlib:
            for iface, face in enumerate(meta.get('dlib:Faces', [])):
                info.append("* '''Face''' (dlib) #" + str(iface + 1))
                info.append("** Score: " + str(round(face['score'], 3)))
                cats = cats.union(print_face_data(face))

            # Faces with opencv's haarcascades:
            for iface, face in enumerate(meta.get('OpenCV:Faces', [])):
                info.append("* '''Face''' (haarcascade) #" + str(iface + 1))
                cats = cats.union(print_face_data(face))

            img.append('</div>')  # Close the image's div

        categories.append(cats)

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
                               ", ".join('[[:' + c + ']]' for c in cats)))
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
    distinct_cats = set(cat for fcats in categories for cat in fcats)
    stats += ["* '''Number of distinct categories used''': {0}"
              .format(len(distinct_cats))]

    stats += ['{{Bar chart',
              '| title = Histogram of files categorized by category name',
              '| label_type = Category (% files analyzed in this category)',
              '| data_type = Number of files in the category',
              '| data_max = ' + str(count)]
    for icat, (catname, numfiles) in \
            enumerate(Counter(cat for fcats in categories
                              for cat in fcats).items()):
        stats += ['| label{0} = {1} ({2:.4f} %)'.format(
                  icat + 1, "[[:" + catname + "]]", 100 * numfiles / count),
                  '| data{0} = {1}'.format(icat + 1, numfiles)]
    stats.append('}}')

    stats += ['{{Bar chart',
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
                pywikibot.error("Invalid alue for -showinfo. It can only be "
                                "cats, info, or all.")
                sys.exit(1)
        elif arg == '-limitsize':
            options[arg[1:]] = int(value) if value != "" else 100
        elif arg == '-cachefiles':
            options[arg[1:]] = value or 'cache'
        elif arg == '-logname':
            options[arg[1:]] = value
        else:
            pywikibot.error('Unknown argument: ' + local_arg)
            sys.exit(1)

    if 'logname' not in options:
        pywikibot.error('-logname required to decide the page to write to.')
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

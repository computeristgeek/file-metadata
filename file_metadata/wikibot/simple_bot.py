#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to show the capabilities of file-metadata. Files are downloaded from the
wiki site and analyzed using file-metadata's analysis routines. Then, the


Syntax:

    wikibot-filemeta-simple [-arguments ...]

Arguments can be:

-showcats      Show only the categories that the file should belong to and not
               the detailed analysis results.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import datetime
import logging
import os
import ssl
import sys
from itertools import chain

from six.moves.urllib.error import URLError

try:
    import pywikibot
except ImportError:
    logging.error("To run the script, pywikibot is required. Please install "
                  "it and try again. The nightly version of pywikibot can be "
                  "installed with `pip install git+https://"
                  "gerrit.wikimedia.org/r/pywikibot/core.git#egg=pywikibot1")
    sys.exit(1)
except RuntimeError as err:
    if (len(err.args) > 0 and
            "No user-config.py found in directory" in err.args[0]):
        logging.error("A user-config.py is require to run the pywikibot "
                      "script. To create the user-config.py run the "
                      "command `wikibot-create-config`.")
        sys.exit(1)
from pywikibot import pagegenerators

from file_metadata.utilities import download, retry
from file_metadata.generic_file import GenericFile


def str_bbox(bbox):
    return ("Left: {left}, Top: {top}, Width: {width}, Height: {height}"
            .format(**bbox))


def handle_meta(meta):
    txt = []
    if options.get('showcats'):
        #################################################################
        # Mime analysis
        mime = meta['File:MIMEType']
        mime_cats = {
            "JPEG files": ('image/jpeg',),
            "GIF files": ('image/gif',),
            "PNG files": ('image/png',),
            "TIFF files": ('image/tiff',),
            "XCF files": ('image/x-xcf', 'application/x-xcf'),
            "FLAC files": ('audio/x-flac',),
            "WAV files": ('audio/x-wav',),
            "MIDI files": ('audio/midi',),
            "DjVu files": ('image/vnd-djvu',),
            "PDF files": ('application/pdf',),
        }
        for cat, mimelist in mime_cats.items():
            if mime in mimelist:
                txt.append('* Category:' + cat)

        #################################################################
        # Software analysis
        # Softwares used:
        softwares = meta.get('Composite:Softwares', [])
        software_cats = {
            'Microsoft ICE': 'Microsoft Image Composite Editor',
            'GNU Plot': 'Gnuplot'
        }
        if len(softwares) > 0:
            for sw in softwares:
                txt.append('* Category:Created with ' +
                           software_cats.get(sw, sw))

        # Screenshot:
        screenshot_softwares = meta.get('Composite:ScreenshotSoftwares', [])
        if len(screenshot_softwares) > 0:
            txt.append('* Category:Screenshots')

        #################################################################
        # Camera analysis
        model = meta.get('EXIF:Model', '')
        if model:
            txt.append("* Category:Taken with " + model)

        #################################################################
        # Barcode analysis
        barcodes = tuple(chain(meta.get('zxing:Barcodes', []),
                               meta.get('zbar:Barcodes', [])))
        if len(barcodes) > 0:
            txt.append('* Category:Barcode')
            bar_cats = {
                "Code 39": ('code_39', 'code39'),
                "Code 93": ('code_93', 'code93'),
                "Code 128": ('code_128', 'code128'),
                "Data Matrix": ('data_matrix',),
                "Quick Response Codes": ('qr_code', 'qrcode'),
            }
            for cat, formats in bar_cats.items():
                if any(bar['format'].lower() in formats for bar in barcodes):
                    txt.append('* Category:' + cat)
    else:
        #################################################################
        # Mime analysis
        txt.append("* Mimetype: " + meta['File:MIMEType'])

        #################################################################
        # Software analysis
        # Softwares used:
        softwares = meta.get('Composite:Softwares', [])
        if len(softwares) > 0:
            txt.append("* Softwares: " + ", ".join(softwares))

        # Screenshot:
        screenshot_softwares = meta.get('Composite:ScreenshotSoftwares', [])
        if len(screenshot_softwares) > 0:
            txt.append("* Screenshot Softwares: " +
                       ", ".join(screenshot_softwares))

        #################################################################
        # Camera analysis
        model = meta.get('EXIF:Model', '')
        if model:
            txt.append("* Camera Model: " + model)

        # Screenshot:
        screenshot_softwares = meta.get('Composite:ScreenshotSoftwares', [])
        if len(screenshot_softwares) > 0:
            txt.append("* Screenshot Softwares: " +
                       ", ".join(screenshot_softwares))

        #################################################################
        # Barcode analysis
        def print_barcode_data(bar):
            txt.append("*** Data: " + bar['data'])
            txt.append("*** Format: " + str(bar['format']))
            txt.append("*** Position : " + str_bbox(bar['bounding box']))

        # Barcodes from zxing:
        for i, bar in enumerate(meta.get('zxing:Barcodes', [])):
            txt.append("** Barcode (zxing) #" + str(i))
            print_barcode_data(bar)

        # Barcodes from zbar:
        for i, bar in enumerate(meta.get('zbar:Barcodes', [])):
            txt.append("** Barcode (zbar) #" + str(i))
            print_barcode_data(bar)

        #################################################################
        # Face analysis
        # Faces with dlib:
        for iface, face in enumerate(meta.get('dlib:Faces', [])):
            txt.append("* Face (dlib) #" + str(iface + 1))
            txt.append("** Score: " + str(round(face['score'], 2)))
            txt.append("** Bounding Box: " + str_bbox(face['position']))

        # Faces with opencv's haarcascades:
        for iface, face in enumerate(meta.get('OpenCV:Faces', [])):
            txt.append("* Face (haarcascade) #" + str(iface + 1))
            txt.append("** Bounding Box: " + str_bbox(face['position']))

    return txt


@retry((ssl.SSLError, URLError), tries=3)
def download_page(page, directory=None, fname=None, timeout=None):
    # Code the filename so that the filesystem definitely supports the name
    fname = fname or page.title(as_filename=True).encode('ascii', 'replace')
    directory = directory or os.path.abspath(os.getcwd())

    fpath = os.path.join(directory, fname)
    download(page.fileUrl(), fpath, timeout=timeout)
    return fpath


def handle_page(page):
    """
    Take a page, download the file in that page and find the best analysis
    class using the `.create()` method of GenericFile.
    """
    txt = []
    if page.namespace() == 'File':
        # File analysis can only be run on pages with files
        start_time = datetime.datetime.now()

        file_path = download_page(page)
        _file = GenericFile.create(file_path)

        txt.append('==== {0} ===='.format(page.title(asLink=True,
                                                     textlink=True)))
        meta = _file.analyze()
        handle_meta(meta)
        end_time = datetime.datetime.now()
        txt.append('Time taken to analyze: ' +
                   str((end_time - start_time).total_seconds()) + "sec")
    return txt


options = {}


def main(*args):
    generator = None
    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()
    if str(site) != "commons:commons":
        pywikibot.warning("The script has not been tested on sites other that "
                          "commons:commons.")

    gen_factory = pagegenerators.GeneratorFactory(site)
    for local_arg in local_args:
        if gen_factory.handleArg(local_arg):
            continue
        arg, sep, value = local_arg.partition(':')
        if arg in ('-showcats',):
            options[arg[1:]] = True
        else:
            raise ValueError('Unknown argument: ' + local_arg)

    generator = gen_factory.getCombinedGenerator(gen=generator)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
    else:
        pregenerator = pagegenerators.PreloadingGenerator(generator)
        for i, page in enumerate(pregenerator):
            if page.exists():
                log = handle_page(page)
                pywikibot.output('\n'.join(log))
                pywikibot.output("")


if __name__ == "__main__":
    main()

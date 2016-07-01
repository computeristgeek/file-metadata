#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import datetime
import os

try:
    import pywikibot
except RuntimeError as err:
    if (len(err.args) > 1 and
            "No user-config.py found in director" in err.args[0]):
        print("A user-config.py is require to run the pywikibot script. To"
              "create the user-config.py run the command "
              "`wikibot-create-config`.")
from pywikibot import pagegenerators

from file_metadata.utilities import download
from file_metadata.generic_file import GenericFile
from file_metadata.image.image_file import ImageFile


def mimetype(_file):
    """
    Use file-metadata's analyze_mimetype() method to fetch the mimetype.
    """
    mime = _file.analyze_mimetype()['File:MIMEType']
    return ["* '''Mimetype:''' " + mime]


def barcode(_file):
    """
    Use file-metadata's analyze_barcode() method to detect whether barcodes
    exist.
    """
    txt = []
    if isinstance(_file, ImageFile):
        # Barcode detection is only for ImageFiles
        barcodes = _file.analyze_barcode()
        if len(barcodes) > 0:
            txt.append("* '''Barcodes found:'''")
        for i, bar in enumerate(barcodes):
            txt.append("** Barcode " + str(i))
            txt.append("*** Data: " + bar['data'])
            txt.append("*** Format: " + str(bar['format']))
            bbox = bar['bounding box']
            txt.append("*** Position (left, top, width, height): "
                       "{left}, {top}, {width}, {height}".format(**bbox))
    return txt


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
        txt += mimetype(_file)
        txt += barcode(_file)

        end_time = datetime.datetime.now()
        txt.append('Time taken to analyze: ' +
                   str((end_time - start_time).total_seconds()) + "sec")
    return txt


def main(*args):
    generator = None
    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()
    if str(site) != "commons:commons":
        pywikibot.warning("The script has not been tested on sites other that "
                          "commons:commons.")
    gen_factory = pagegenerators.GeneratorFactory(site)
    for arg in local_args:
        gen_factory.handleArg(arg)

    generator = gen_factory.getCombinedGenerator(gen=generator)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
    else:
        pregenerator = pagegenerators.PreloadingGenerator(generator)
        for i, page in enumerate(pregenerator):
            if page.exists():
                log = handle_page(page)
                print('\n'.join(log))
                print("")


if __name__ == "__main__":
    main()

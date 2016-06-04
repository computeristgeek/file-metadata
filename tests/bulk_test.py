# -*- coding: utf-8 -*-
"""
This file contains large scale bulk tests to check whether the code is
running find or not. This is tested using a large number of files from
commons.wikimedia.org.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import json
import os
import ssl
import types

import pytest
from retry import retry

from file_metadata._compat import URLError, str_type, makedirs
from file_metadata.generic_file import GenericFile
from file_metadata.utilities import download
from tests import is_travis, unittest, CACHE_DIR

try:
    import pywikibot
except ImportError as err:
    raise unittest.SkipTest("Module pywikibot not found. Please install it "
                            "to run bulk tests.")
except RuntimeError as err:
    pywikibot = err
    raise unittest.SkipTest('pywikibot requires a user-config.py, which was '
                            'not found. Please create one and then run '
                            'bulk tests.')

from pywikibot import pagegenerators


def dump_log(data, logname, _type='text', header=None):
    """
    Dump the given info into a mediawiki file in the User namespace
    'User:<Username>/logs/<logname>'.

    :param data:    The data to log.
    :param logname: The name of the page to save it in.
    :param _type:   The type of data being logged. json or text.
    :param header:  The header to add to the page before dumping data.
    """
    if data is not None:
        if _type == 'json':
            logs = '<pre>{0}</pre>'.format(json.dumps(
                data, sort_keys=True, indent=2, separators=(',', ': ')))
        elif _type == 'text':
            if isinstance(data, str_type):
                logs = data
            elif isinstance(data, (tuple, list, types.GeneratorType)):
                logs = "\n".join(data)
            else:
                raise ValueError('Unexpected output got. Expected str, tuple, '
                                 'list or generator when _type=text is given.')
        else:
            raise ValueError('Unexpected value "{0} given."'.format(_type))

        if header is not None:
            logs = header + '\n' + logs

        site = pywikibot.Site()
        site.login()

        page = pywikibot.Page(
            site, 'User:' + site.username() + '/logs/' + logname)
        page.put(logs, "Logged with file-metadata's dump_log()")


@pytest.mark.timeout(60 * 60)
class PyWikiBotTestHelper(unittest.TestCase):

    def setUp(self):
        self.site = pywikibot.Site()
        self.site.login()

        makedirs(CACHE_DIR, exist_ok=True)

    @staticmethod
    @retry((ssl.SSLError, URLError), tries=5)
    def download_page(page, fname=None):
        url = page.fileUrl()
        fname = fname or page.title(as_filename=True)
        fpath = os.path.join(CACHE_DIR, fname)
        download(url, fpath)
        return fpath

    def factory(self, args, fname=None):
        """
        Use pywikibot to fetch pages based on the given arguments. If the
        system is detected to be TRAVIS, it auto deletes the file afterwards.

        :param args:  The args to give to pywikibot
        :param fname: If this is given, the file is stored in this filename.
        :return:      A generator with the pages asked
        """
        gen_factory = pagegenerators.GeneratorFactory(self.site)
        for arg in args:
            gen_factory.handleArg(arg)

        generator = gen_factory.getCombinedGenerator()
        if not generator:
            self.fail('No generator was asked from the factory.')
        else:
            pregen = pagegenerators.PreloadingGenerator(generator,
                                                        groupsize=50)
            for page in pregen:
                if page.exists() and not page.isRedirectPage():
                    page_path = self.download_page(page, fname=fname)
                    yield page, page_path
                    if is_travis():
                        os.remove(page_path)


class BulkCategoryTest(PyWikiBotTestHelper):

    def _test_mimetype_category(self, cat, limit=10000):
        log = []
        for count, (page, path) in enumerate(self.factory(
                ['-catr:' + str(cat), '-limit:' + str(limit), '-ns:File'])):

            print(count + 1, '. Analyzing', page.title(underscore=False))
            if (count + 1) % 500 == 1:
                log.append('== {0} to {1} =='.format(count + 1, count + 500))

            _file = GenericFile.create(path)
            log.append('* [[:{0}'.format(
                       page.title(underscore=True, asLink=True)[2:]))
            # log.append("** '''URL''': " + page.fileUrl())
            mime = _file.analyze_mimetype().get('File:MIMEType', "ERROR")
            log.append("** '''Mime Type''': " + mime)
            if mime == 'application/ogg':
                _type = _file.analyze_exiftool().get('File:FileType', 'ERROR')
                log.append("** '''File type''': " + _type)

        dump_log(log, logname='Category ' + cat,
                 header="This page holds all the analysis done on the "
                        "files of the category [[:Category:" + cat + "]].\n")

    def test_mimetype_png_files(self):
        self._test_mimetype_category('PNG files')

    def test_mimetype_svg_files(self):
        self._test_mimetype_category('SVG files')

    def test_mimetype_jpeg_files(self):
        self._test_mimetype_category('JPEG files')

    def test_mimetype_gif_files(self):
        self._test_mimetype_category('GIF files')

    def test_mimetype_tiff_files(self):
        self._test_mimetype_category('TIFF files')

    def test_mimetype_ogv_videos(self):
        self._test_mimetype_category('Ogv videos')

    def test_mimetype_animated_gif_files(self):
        self._test_mimetype_category('Animated GIF files')

    def test_mimetype_animated_png(self):
        self._test_mimetype_category('Animated PNG')

    def test_mimetype_animated_svg(self):
        self._test_mimetype_category('Animated SVG')

    def test_mimetype_audio(self):
        self._test_mimetype_category('FLAC files')

    def test_mimetype_wav_files(self):
        self._test_mimetype_category('WAV files')

    def test_mimetype_ogg_sound_files(self):
        self._test_mimetype_category('Ogg sound files')

    def test_mimetype_midi_files(self):
        self._test_mimetype_category('MIDI files')

    def test_mimetype_djvu_files(self):
        self._test_mimetype_category('DjVu files')

    def test_mimetype_xcf_files(self):
        self._test_mimetype_category('XCF files')

    def test_mimetype_pdf_files(self):
        self._test_mimetype_category('PDF files')

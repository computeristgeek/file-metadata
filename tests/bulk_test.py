# -*- coding: utf-8 -*-
"""
This file contains large scale bulk tests to check whether the code is
running find or not. This is tested using a large number of files from
commons.wikimedia.org.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import datetime
import json
import os
import ssl
import subprocess
import tempfile
import types
from collections import Counter

import pytest
from retry import retry
from six import string_types
from six.moves.urllib.error import URLError

from file_metadata._compat import makedirs
from file_metadata.generic_file import GenericFile
from file_metadata.image.image_file import ImageFile
from file_metadata.utilities import download
from tests import is_travis, is_toolserver, unittest, CACHE_DIR

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
            if isinstance(data, string_types):
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
    __test__ = True

    def setUp(self):
        self.site = pywikibot.Site()
        self.site.login()
        if is_toolserver():
            self.cache_dir = tempfile.mkdtemp(prefix="dir_file_metadata_")
        else:
            self.cache_dir = CACHE_DIR
        makedirs(self.cache_dir, exist_ok=True)

    @retry((ssl.SSLError, URLError), tries=5)
    def download_page(self, page, fname=None, timeout=None):
        url = page.fileUrl()
        fname = fname or page.title(as_filename=True).encode('ascii',
                                                             'replace')
        fpath = os.path.join(self.cache_dir, fname)
        download(url, fpath, timeout=timeout)
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

        parsed_pages = set()
        generator = gen_factory.getCombinedGenerator()
        if not generator:
            self.fail('No generator was asked from the factory.')
        else:
            pregen = pagegenerators.PreloadingGenerator(generator,
                                                        groupsize=50)
            for page in pregen:
                if page.exists() and not page.isRedirectPage():
                    if page.title() in parsed_pages:
                        continue
                    try:
                        page_path = self.download_page(page, fname=fname,
                                                       timeout=15 * 60)
                    except URLError:
                        # URLError is raised if the download timesout.
                        continue
                    yield page, page_path
                    parsed_pages.add(page.title())
                    if is_travis():
                        os.remove(page_path)


class BulkCategoryTest(PyWikiBotTestHelper):

    def _test_file(self, page, path):
        log = []
        stats = {'mime': None}
        txt, im = [], []
        # First cell has text info
        # Second cell has image bounding boxes if applicable

        start_time = datetime.datetime.now()
        _file = GenericFile.create(path)
        log.append('===== {0} ====='.format(
                   page.title(asLink=True, textlink=True)))

        # Analyze mime and file type
        mime = _file.analyze_mimetype().get('File:MIMEType', "ERROR")
        stats['mime'] = mime
        txt.append("* '''Mime Type''': " + mime)
        if mime == 'application/ogg':
            _type = _file.analyze_exifdata().get('File:FileType', 'ERROR')
            txt.append("* '''File type''': " + _type)

        if isinstance(_file, ImageFile):
            # Analyze softwares
            softwares = _file.analyze_softwares()
            if 'Composite:Softwares' in softwares:
                softwares = softwares['Composite:Softwares']
                if isinstance(softwares, tuple):
                    softwares = ", ".join(softwares)
                txt.append("* '''Softwares''': " + softwares)

            # Analyze color
            col_avg = _file.analyze_color_average()
            if col_avg:
                txt.append("* '''Average RGB value''': " +
                           ', '.join(map(str, col_avg['Color:AverageRGB'])))
                txt.append("* '''Closest Pantone color''': " +
                           ', '.join(col_avg['Color:ClosestLabeledColor']))

            # Fill second column (image cell) for ImageFiles
            if _file.fetch('ndarray').ndim in (2, 3):
                # Only for 2 dimension images (ndim 2 or 3)
                height, width = _file.fetch('ndarray').shape[:2]
                if width > height:
                    scale = min(200, width) * 1.0 / width
                else:
                    scale = min(200, height) * 1.0 / height
                scaled_h, scaled_w = int(height * scale), int(width * scale)

                im.append('<div style="position:relative;">')
                im.append('{0}|{1}x{2}px]]'.format(
                          page.title(underscore=False, asLink=True)[:-2],
                          scaled_w, scaled_h))
                box = ('<div class="position-marker file-meta-{css_class}" '
                       'style="position:absolute; '
                       'left:{left}px; top:{top}px; width:{width}px; '
                       'height:{height}px; border:2px solid #{color};"></div>')

                # Analyze barcodes
                barcode_data = {}
                try:
                    barcode_data = _file.analyze_barcode()
                except subprocess.CalledProcessError:
                    txt.append("* '''Barcodes ERROR:''' Unsupported file type")
                barcodes = barcode_data.get('zxing:Barcodes', [])
                if len(barcodes) > 0:
                    txt.append("* '''Barcodes found:'''")
                for ibar, bar in enumerate(barcodes):
                    txt.append("** Barcode #" + str(ibar + 1))
                    txt.append("*** Data: " + bar['data'])
                    txt.append("*** Format: " + str(bar['format']))
                    txt.append("*** Bounding Box: " + str(bar['bounding box']))
                    box_kwargs = {k: int(v * scale)
                                  for k, v in bar['bounding box'].items()}
                    box_kwargs.update({"color": "ff0000",
                                       "css_class": "barcode"})
                    im.append(box.format(**box_kwargs))

                # Analyze faces
                faces = _file.analyze_facial_landmarks().get('dlib:Faces', [])
                if len(faces) > 0:
                    txt.append("* '''Faces found:'''")
                for iface, face in enumerate(faces):
                    txt.append("** Face #" + str(iface + 1))
                    txt.append("** Score: " + str(round(face['score'], 2)))
                    txt.append("** Bounding Box: " + str(face['position']))
                    box_kwargs = {k: int(v * scale)
                                  for k, v in face['position'].items()}
                    box_kwargs.update({"color": "00ff00",
                                       "css_class": "face"})
                    im.append(box.format(**box_kwargs))

        end_time = datetime.datetime.now()
        secs = (end_time - start_time).total_seconds()
        txt.append("* '''Time taken''': " + str(secs))

        # Make a table for text and image
        log += (['{| class="wikitable"', '|'] + txt + ['|'] + im + ['|}'])
        return log, stats

    def _test_category(self, category, limit=10000):
        log = []
        cat = pywikibot.Category(self.site, category)

        stats = {'count': 0, 'mime': [], 'ext': [],
                 'start_time': datetime.datetime.now()}
        for count, (page, path) in enumerate(self.factory(
                ['-catr:' + cat.title(withNamespace=False, underscore=True),
                 '-limit:' + str(limit),
                 '-ns:File'])):

            print(count + 1, '. Analyzing', page.title(underscore=False))
            if (count + 1) % 500 == 1:
                log.append('== {0} to {1} =='.format(count + 1, count + 500))
            _log, _stat = self._test_file(page, path)
            log += _log

            stats['count'] = count + 1
            stats['ext'].append(os.path.splitext(page.title())[-1])
            stats['mime'].append(_stat['mime'])

        stats['end_time'] = datetime.datetime.now()
        stats['timetaken'] = (stats['end_time'] -
                              stats['start_time']).total_seconds()

        title = 'Category {0}'.format(cat.title(underscore=False,
                                                withNamespace=False))
        summary = ["Analyis from files of " + cat.title(asLink=True,
                                                        textlink=True),
                   "* '''Time taken''': " + str(stats['timetaken']),
                   "* '''Files analyzed''': " + str(stats['count']),
                   "* '''MIME type stats''': "]
        for mime, count in Counter(stats['mime']).items():
            summary.append("** " + str(mime) + " - " + str(count))
        summary.append("* '''Enxtension Stats''': ")
        for ext, count in Counter(stats['ext']).items():
            summary.append("** " + str(ext) + " - " + str(count))

        dump_log(log, logname=title, header="\n".join(summary))

    def test_png_files(self):
        self._test_category('PNG files')

    def test_svg_files(self):
        self._test_category('SVG files')

    def test_jpeg_files(self):
        self._test_category('JPEG files')

    def test_gif_files(self):
        self._test_category('GIF files')

    def test_tiff_files(self):
        self._test_category('TIFF files')

    def test_ogv_videos(self):
        self._test_category('Ogv videos', 2000)  # Takes ~1Hr in travis

    def test_animated_gif_files(self):
        self._test_category('Animated GIF files')

    def test_animated_png(self):
        self._test_category('Animated PNG')

    def test_animated_svg(self):
        self._test_category('Animated SVG')

    def test_flac_files(self):
        self._test_category('FLAC files')

    def test_wav_files(self):
        self._test_category('WAV files')

    def test_ogg_sound_files(self):
        self._test_category('Ogg sound files', 8000)  # Takes ~1Hr in travis

    def test_midi_files(self):
        self._test_category('MIDI files')

    def test_djvu_files(self):
        self._test_category('DjVu files', 5000)  # Takes ~1Hr in travis

    def test_xcf_files(self):
        self._test_category('XCF files')

    def test_pdf_files(self):
        self._test_category('PDF files', 5000)

    def test_barcode(self):
        self._test_category('Barcode')

    def test_images_from_the_state_library_of_queensland(self):
        self._test_category('Images from the State Library of Queensland')

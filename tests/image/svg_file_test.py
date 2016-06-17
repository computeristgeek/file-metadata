# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os

from file_metadata.image.svg_file import SVGFile
from tests import fetch_file, unittest


class SVGFileTest(unittest.TestCase):

    def test_svg_fetch_filename_raster(self):
        uut = SVGFile(fetch_file('image_svg_xml.svg'))
        self.assertTrue(uut.fetch('filename_raster').endswith('.png'))

        self.assertEqual(len(uut.temp_filenames), 1)
        name = tuple(uut.temp_filenames)[0]
        self.assertTrue(os.path.exists(name))
        uut.close()
        self.assertFalse(os.path.exists(name))

    def test_fetch_svg_ndarray_application_xml(self):
        with SVGFile(fetch_file('application_xml.svg')) as uut:
            self.assertEqual(uut.fetch('ndarray').shape, (369, 445, 4))

    def test_fetch_svg_ndarray(self):
        with SVGFile(fetch_file('image_svg_xml.svg')) as uut:
            self.assertEqual(uut.fetch('ndarray').shape, (100, 100))

    def test_fetch_svg_ndarray_text_html(self):
        with SVGFile(fetch_file('text_html.svg')) as uut:
            self.assertEqual(uut.fetch('ndarray').shape, (260, 200, 4))

    def test_fetch_svg_ndarray_text_plain(self):
        with SVGFile(fetch_file('text_plain.svg')) as uut:
            self.assertEqual(uut.fetch('ndarray').shape, (300, 300, 3))

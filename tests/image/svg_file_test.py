# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.image.svg_file import SVGFile
from tests import fetch_file, unittest


class SVGFileTest(unittest.TestCase):

    def test_fetch_svg_ndarray_application_xml(self):
        _file = SVGFile(fetch_file('application_xml.svg'))
        self.assertEqual(_file.fetch('ndarray').shape, (369, 445, 4))

    def test_fetch_svg_ndarray(self):
        _file = SVGFile(fetch_file('image_svg_xml.svg'))
        self.assertEqual(_file.fetch('ndarray').shape, (100, 100))

    def test_fetch_svg_ndarray_text_html(self):
        _file = SVGFile(fetch_file('text_html.svg'))
        self.assertEqual(_file.fetch('ndarray').shape, (260, 200, 4))

    def test_fetch_svg_ndarray_text_plain(self):
        _file = SVGFile(fetch_file('text_plain.svg'))
        self.assertEqual(_file.fetch('ndarray').shape, (300, 300, 3))

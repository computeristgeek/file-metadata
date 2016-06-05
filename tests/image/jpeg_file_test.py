# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.image.jpeg_file import JPEGFile
from tests import fetch_file, unittest


class JPEGFileTest(unittest.TestCase):

    def test_filename_zxing(self):
        _file = JPEGFile(fetch_file('barcode_cmyk.jpg'))
        self.assertIn('tmp_file_metadata', _file.fetch('filename_zxing'))


class JPEGFileBarcodesTest(unittest.TestCase):

    def test_jpeg_qrcode(self):
        _file = JPEGFile(fetch_file('qrcode.jpg'))
        data = _file.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'QR_CODE')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'http://www.wikipedia.com')

    def test_jpeg_cmyk(self):
        _file = JPEGFile(fetch_file('barcode_cmyk.jpg'))
        data = _file.analyze_barcode()
        self.assertNotIn('zxing:Barcodes', data)
        # Although no barcode is detected, this test is to ensure that the
        # "Unsupported File Format" error doesn't occur for CMYK files.


class JPEGFileCreateTest(unittest.TestCase):

    def test_create_jpeg_file(self):
        for fname in ['qrcode.jpg', 'barcode_cmyk.jpg']:
            self.assertTrue(isinstance(
                JPEGFile.create(fetch_file(fname)), JPEGFile),
                'File "{0}" was not of type jpeg'.format(fname))

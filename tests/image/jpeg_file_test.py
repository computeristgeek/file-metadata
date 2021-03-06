# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os

from file_metadata.image.jpeg_file import JPEGFile
from tests import fetch_file, unittest


class JPEGFileTest(unittest.TestCase):

    def test_filename_zxing(self):
        uut = JPEGFile(fetch_file('cmyk.jpg'))
        self.assertIn('tmp_file_metadata', uut.fetch('filename_zxing'))

        self.assertEqual(len(uut.temp_filenames), 1)
        name = tuple(uut.temp_filenames)[0]
        self.assertTrue(os.path.exists(name))
        uut.close()
        self.assertFalse(os.path.exists(name))


class JPEGFileBarcodeZXingTest(unittest.TestCase):

    def test_jpeg_qrcode(self):
        with JPEGFile(fetch_file('qrcode.jpg')) as uut:
            data = uut.analyze_barcode_zxing()
            self.assertIn('zxing:Barcodes', data)
            self.assertEqual(len(data['zxing:Barcodes']), 1)
            self.assertEqual(data['zxing:Barcodes'][0]['format'], 'QR_CODE')
            self.assertEqual(data['zxing:Barcodes'][0]['data'],
                             'http://www.wikipedia.com')

    def test_jpeg_cmyk(self):
        with JPEGFile(fetch_file('cmyk.jpg')) as uut:
            data = uut.analyze_barcode_zxing()
            self.assertNotIn('zxing:Barcodes', data)
            # Although no barcode is detected, this test is to ensure that the
            # "Unsupported File Format" error doesn't occur for CMYK files.

    def test_jpeg_unknown_cmyk(self):
        with JPEGFile(fetch_file('unknown_cmyk.jpg')) as uut:
            data = uut.analyze_barcode_zxing()
            self.assertNotIn('zxing:Barcodes', data)
            # Although no barcode is detected, this test is to ensure that the
            # "Unsupported File Format" error doesn't occur for CMYK files.

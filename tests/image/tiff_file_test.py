# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os

from file_metadata.image.tiff_file import TIFFFile
from tests import fetch_file, unittest


class TIFFFileTest(unittest.TestCase):

    def test_filename_zxing(self):
        uut = TIFFFile(fetch_file('example.tiff'))
        self.assertIn('tmp_file_metadata', uut.fetch('filename_zxing'))

        self.assertEqual(len(uut.temp_filenames), 1)
        name = tuple(uut.temp_filenames)[0]
        self.assertTrue(os.path.exists(name))
        uut.close()
        self.assertFalse(os.path.exists(name))


class TIFFFileBarcodeZXingTest(unittest.TestCase):

    def test_barcode_zxing_tiff(self):
        with TIFFFile(fetch_file('example.tiff')) as uut:
            data = uut.analyze_barcode_zxing()
            self.assertNotIn('zxing:Barcodes', data)
            # Although no barcode is detected, this test is to ensure that the
            # "Unsupported File Format" error doesn't occur.

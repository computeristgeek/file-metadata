# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import pytest

from file_metadata.image.image_file import ImageFile
from tests import fetch_file, unittest


class ImageFileTest(unittest.TestCase):

    def setUp(self):
        self.ball_png = ImageFile(fetch_file('ball.png'))
        self.red_png = ImageFile(fetch_file('red.png'))
        self.green_png = ImageFile(fetch_file('green.png'))
        self.blue_png = ImageFile(fetch_file('blue.png'))

    def test_ndarray_read(self):
        self.assertEqual(self.ball_png.fetch('ndarray').shape, (226, 226, 4))

    def test_color_average(self):
        data = self.red_png.analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (255, 0, 0))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 17-1462 TPX (Flame)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (244, 81, 44))

        data = self.green_png.analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (0, 255, 0))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 15-0545 TPX (Jasmine Green)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (129, 204, 69))

        data = self.blue_png.analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (0, 0, 255))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 18-3949 TPX (Dazzling blue)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (46, 77, 167))


# Increase the timeout as the first time it will need to download the
# shape predictor data ~60MB
@pytest.mark.timeout(300)
class ImageFileFaceLandmarksTest(unittest.TestCase):

    def setUp(self):
        self.mona_lisa = ImageFile(fetch_file('mona_lisa.jpg'))
        self.baby_face = ImageFile(fetch_file('baby_face.jpg'))
        self.monkey_face = ImageFile(fetch_file('monkey_face.jpg'))

    def test_facial_landmarks_monkey_face(self):
        data = self.monkey_face.analyze_facial_landmarks()
        self.assertEqual(data, {})

    def test_facial_landmarks_mona_lisa(self):
        data = self.mona_lisa.analyze_facial_landmarks(with_landmarks=True)
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)
        face = data['dlib:Faces'][0]

        self.assertEqual(face['left_eye'], (288, 252))
        self.assertEqual(face['right_eye'], (361, 251))
        self.assertEqual(face['nose'], (325, 318))
        self.assertEqual(face['mouth'], (321, 338))

    def test_facial_landmarks_baby_face(self):
        data = self.baby_face.analyze_facial_landmarks()
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)


class ImageFileBarcodesTest(unittest.TestCase):

    def setUp(self):
        self.mona_lisa = ImageFile(fetch_file('mona_lisa.jpg'))
        self.multibarcodes = ImageFile(fetch_file('multibarcodes.png'))
        self.barcode = ImageFile(fetch_file('barcode.png'))
        self.qrcode = ImageFile(fetch_file('qrcode.jpg'))
        self.dmtx = ImageFile(fetch_file('datamatrix.png'))

    def test_mona_lisa(self):
        data = self.mona_lisa.analyze_barcode()
        self.assertEqual(data, {})

    def test_barcode(self):
        data = self.barcode.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'CODABAR')
        self.assertEqual(data['zxing:Barcodes'][0]['data'], '137255')

    def test_qrcode(self):
        data = self.qrcode.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'QR_CODE')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'http://www.wikipedia.com')

    def test_dmtx(self):
        data = self.dmtx.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'DATA_MATRIX')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'Wikipedia, the free encyclopedia')

    def test_multiple_barcodes(self):
        data = self.multibarcodes.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 2)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'CODE_128')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         '2LUS94941+67000000')
        self.assertEqual(data['zxing:Barcodes'][1]['format'], 'ITF')
        self.assertEqual(data['zxing:Barcodes'][1]['data'], '054804124097')


class ImageFileCreateTest(unittest.TestCase):

    def test_create_image_file(self):
        for fname in ['red.png', 'red.svg', 'example.tiff']:
            self.assertTrue(isinstance(
                ImageFile.create(fetch_file(fname)), ImageFile),
                'File "{0}" was not of type image'.format(fname))

    def test_create_jpeg_file(self):
        from file_metadata.image.jpeg_file import JPEGFile
        for fname in ['qrcode.jpg', 'barcode_cmyk.jpg']:
            self.assertTrue(isinstance(
                ImageFile.create(fetch_file(fname)), JPEGFile),
                'File "{0}" was not of type jpeg'.format(fname))

    def test_create_xcf_file(self):
        from file_metadata.image.xcf_file import XCFFile
        for fname in ['blank.xcf']:
            self.assertTrue(isinstance(
                ImageFile.create(fetch_file(fname)), XCFFile),
                'File "{0}" was not of type xcf'.format(fname))

# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import numpy
import pytest

from file_metadata.image.image_file import ImageFile
from tests import fetch_file, unittest


class ImageFileTest(unittest.TestCase):

    def setUp(self):
        self.ball_png = ImageFile(fetch_file('ball.png'))

    def test_ndarray_read(self):
        self.assertEqual(self.ball_png.fetch('ndarray').shape, (226, 226, 4))


class ImageFileColorAverageTest(unittest.TestCase):

    def test_color_average_rgb_image(self):
        data = ImageFile(fetch_file('red.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (255, 0, 0))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 17-1462 TPX (Flame)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (244, 81, 44))

        data = ImageFile(fetch_file('green.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (0, 255, 0))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 15-0545 TPX (Jasmine Green)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (129, 204, 69))

        data = ImageFile(fetch_file('blue.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (0, 0, 255))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 18-3949 TPX (Dazzling blue)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (46, 77, 167))

    def test_color_average_rgba_image(self):
        data = ImageFile(fetch_file('ball.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (113.705, 113.705, 113.705))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 18-5102 TPX (Brushed Nickel)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (122, 118, 117))

    def test_color_average_greyscale_image(self):
        data = ImageFile(fetch_file('barcode.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (170.579, 170.579, 170.579))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 15-4306 TPX (Belgian Block)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (167, 173, 170))

    def test_color_average_animated_image(self):
        data = ImageFile(fetch_file('animated.gif')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (227.326, 224.414, 224.414))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 13-4108 TPX (Nimbus Cloud)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (223, 223, 227))

    def test_color_average_unknown_format(self):
        _file = ImageFile(fetch_file('red.png'))
        _file.fetch('filename')
        _file.fetch.cache.update({
            str((_file, 'ndarray')) + str({}): numpy.ndarray([1])})
        data = _file.analyze_color_average()
        self.assertEqual(data, {})


# Increase the timeout as the first time it will need to download the
# shape predictor data ~60MB
@pytest.mark.timeout(300)
class ImageFileFaceLandmarksTest(unittest.TestCase):

    def test_facial_landmarks_monkey_face(self):
        _file = ImageFile(fetch_file('monkey_face.jpg'))
        data = _file.analyze_facial_landmarks()
        self.assertEqual(data, {})

    def test_facial_landmarks_mona_lisa(self):
        _file = ImageFile(fetch_file('mona_lisa.jpg'))
        data = _file.analyze_facial_landmarks(with_landmarks=True)
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)
        face = data['dlib:Faces'][0]

        self.assertEqual(face['left_eye'], (288, 252))
        self.assertEqual(face['right_eye'], (361, 251))
        self.assertEqual(face['nose'], (325, 318))
        self.assertEqual(face['mouth'], (321, 338))

    def test_facial_landmarks_baby_face(self):
        _file = ImageFile(fetch_file('baby_face.jpg'))
        data = _file.analyze_facial_landmarks(with_landmarks=False)
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)

        face = data['dlib:Faces'][0]
        self.assertNotIn('left_eye', face)
        self.assertNotIn('right_eye', face)
        self.assertNotIn('nose', face)
        self.assertNotIn('mouth', face)
        self.assertIn('position', face)

    def test_facial_landmarks_animated_image(self):
        _file = ImageFile(fetch_file('animated.gif'))
        data = _file.analyze_facial_landmarks()
        self.assertEqual(data, {})


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
        for fname in ['red.png', 'example.tiff']:
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

    def test_create_svg_file(self):
        from file_metadata.image.svg_file import SVGFile
        for fname in ['text_html.svg', 'text_plain.svg', 'image_svg_xml.svg',
                      'application_xml.svg']:
            self.assertTrue(isinstance(
                ImageFile.create(fetch_file(fname)), SVGFile),
                'File "{0}" was not of type svg'.format(fname))

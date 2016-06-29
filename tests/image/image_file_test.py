# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import pytest

from file_metadata.image.image_file import ImageFile
from tests import fetch_file, unittest


class ImageFileTest(unittest.TestCase):

    def test_ndarray_read(self):
        _file = ImageFile(fetch_file('ball.png'))
        self.assertEqual(_file.fetch('ndarray').shape, (226, 226, 4))

    def test_huge_ndarray(self):
        _file = ImageFile(fetch_file('huge.png'))
        self.assertEqual(_file.fetch('ndarray').shape, (0,))


class ImageFileSoftwaresTest(unittest.TestCase):

    def test_created_with_unknown(self):
        _file = ImageFile(fetch_file('red.svg'))
        self.assertEqual(_file.analyze_softwares(), {})

    def test_created_with_inkscape(self):
        _file = ImageFile(fetch_file('created_with_inkscape.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Inkscape')

    def test_created_with_matlab(self):
        _file = ImageFile(fetch_file('created_with_matlab.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'MATLAB')

    def test_created_with_imagemagick(self):
        _file = ImageFile(fetch_file('created_with_imagemagick.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'ImageMagick')

    def test_created_with_adobe_imageready(self):
        _file = ImageFile(fetch_file('created_with_adobe_imageready.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe ImageReady')

    def test_created_with_adobe_photoshop(self):
        _file = ImageFile(fetch_file('created_with_adobe_photoshop.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe Photoshop')

    def test_created_with_adobe_photoshop_express(self):
        _file = ImageFile(fetch_file(
            'created_with_adobe_photoshop_express.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe Photoshop Express')

    def test_created_with_adobe_photoshop_elements(self):
        _file = ImageFile(fetch_file(
            'created_with_adobe_photoshop_elements.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe Photoshop Elements')

    def test_created_with_picasa(self):
        _file = ImageFile(fetch_file('created_with_picasa.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Picasa')

    def test_created_with_gimp(self):
        _file = ImageFile(fetch_file('created_with_gimp.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'GIMP')

    def test_created_with_gnu_octave(self):
        _file = ImageFile(fetch_file('created_with_gnu_octave.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'GNU Plot')

    def test_created_with_gnuplot(self):
        _file = ImageFile(fetch_file('created_with_gnuplot.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'GNU Plot')

    def test_created_with_chemtool(self):
        _file = ImageFile(fetch_file('created_with_chemtool.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Chemtool')

    def test_created_with_vectorfieldplot(self):
        _file = ImageFile(fetch_file('created_with_vectorfieldplot.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'VectorFieldPlot')

    def test_created_with_stella(self):
        _file = ImageFile(fetch_file('created_with_stella.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Stella')

    def test_created_with_microsoft_image_composite_editor(self):
        _file = ImageFile(fetch_file(
            'created_with_microsoft_image_composite_editor.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Microsoft ICE')


class ImageFileColorInfoTest(unittest.TestCase):

    def test_color_info_rgb_image(self):
        data = ImageFile(fetch_file('red.png')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (255, 0, 0))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 17-1462 TPX (Flame)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (244, 81, 44))
        self.assertEqual(data['Color:NumberOfGreyShades'], 1)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.004)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0)

    def test_color_info_rgba_image(self):
        data = ImageFile(fetch_file('ball.png')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (113.705, 113.705, 113.705))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 18-5102 TPX (Brushed Nickel)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (122, 118, 117))
        self.assertEqual(data['Color:NumberOfGreyShades'], 2)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.008)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.016)

    def test_color_info_greyscale_image(self):
        data = ImageFile(fetch_file('barcode.png')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (170.579, 170.579, 170.579))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 15-4306 TPX (Belgian Block)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (167, 173, 170))
        self.assertEqual(data['Color:NumberOfGreyShades'], 2)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.008)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.268)

    def test_color_info_animated_image(self):
        data = ImageFile(fetch_file('animated.gif')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (227.326, 224.414, 224.414))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 13-4108 TPX (Nimbus Cloud)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (223, 223, 227))
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.008)
        self.assertNotIn('Color:EdgeRatio', data)
        self.assertNotIn('Color:NumberOfGreyShades', data)

    def test_color_info_non_line_drawings(self):
        data = ImageFile(fetch_file('mona_lisa.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (82.457, 74.157, 63.756))
        self.assertEqual(data['Color:NumberOfGreyShades'], 204)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.626)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.290)

        data = ImageFile(fetch_file('baby_face.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (131.434, 130.707, 120.324))
        self.assertEqual(data['Color:NumberOfGreyShades'], 203)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.442)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.303)

        data = ImageFile(fetch_file(
            'michael_jackson.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (120.288, 65.377, 70.155))
        self.assertEqual(data['Color:NumberOfGreyShades'], 83)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.154)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.273)

    def test_color_info_line_drawings(self):
        data = ImageFile(fetch_file(
            'simple_line_drawing.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (243.131, 243.131, 243.131))
        self.assertEqual(data['Color:NumberOfGreyShades'], 5)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.016)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.191)

        data = ImageFile(fetch_file(
            'detailed_line_drawing.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (229.461, 229.461, 229.461))
        self.assertEqual(data['Color:NumberOfGreyShades'], 1)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.004)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.112)

        data = ImageFile(fetch_file(
            'very_detailed_line_drawing.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (135.896, 135.896, 135.896))
        self.assertEqual(data['Color:NumberOfGreyShades'], 8)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.012)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.283)

        data = ImageFile(fetch_file(
            'dark_line_drawing.jpg')).analyze_color_info()
        self.assertIn('Color:AverageRGB', data)
        self.assertEqual(data['Color:AverageRGB'], (204.207, 204.207, 204.207))
        self.assertEqual(data['Color:NumberOfGreyShades'], 2)
        self.assertEqual(round(data['Color:PercentFrequentColors'], 3), 0.008)
        self.assertEqual(round(data['Color:EdgeRatio'], 3), 0.093)


class ImageFileCarHAARCascadesTest(unittest.TestCase):

    def test_car_haarcascade_(self):
        with ImageFile(fetch_file('.jpg')) as uut:
            data = uut.analyze_face_haarcascades()
            self.assertIn('OpenCV:Cars', data)
            self.assertEqual(len(data['OpenCV:Cars']), 1)

            car = data['OpenCV:Cars'][0]
            self.assertEqual(car['position'], {"height": None})
            self.assertEqual(car['coverage'], -1)


class ImageFileFaceHAARCascadesTest(unittest.TestCase):

    def test_face_haarcascade_charlie_chaplin(self):
        with ImageFile(fetch_file('charlie_chaplin.jpg')) as uut:
            data = uut.analyze_face_haarcascades()
            self.assertIn('OpenCV:Faces', data)
            self.assertEqual(len(data['OpenCV:Faces']), 1)

            face = data['OpenCV:Faces'][0]
            self.assertEqual(face['nose'], (776, 688))
            self.assertEqual(face['mouth'], (735, 794))

    def test_face_haarcascade_mona_lisa(self):
        with ImageFile(fetch_file('mona_lisa.jpg')) as uut:
            data = uut.analyze_face_haarcascades()
            self.assertIn('OpenCV:Faces', data)
            self.assertEqual(len(data['OpenCV:Faces']), 1)

            face = data['OpenCV:Faces'][0]
            self.assertEqual(face['nose'], (318, 310))
            self.assertEqual(face['mouth'], (325, 341))

    def test_face_haarcascade_monkey_face(self):
        _file = ImageFile(fetch_file('monkey_face.jpg'))
        data = _file.analyze_face_haarcascades()
        self.assertEqual(data, {})

    def test_face_haarcascade_baby_face(self):
        _file = ImageFile(fetch_file('baby_face.jpg'))
        data = _file.analyze_face_haarcascades()
        self.assertIn('OpenCV:Faces', data)
        self.assertEqual(len(data['OpenCV:Faces']), 1)

        face = data['OpenCV:Faces'][0]
        self.assertEqual(face['mouth'], (851, 1381))
        self.assertIn('position', face)

    def test_face_haarcascade_animated_image(self):
        _file = ImageFile(fetch_file('animated.gif'))
        data = _file.analyze_face_haarcascades()
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

        self.assertEqual(len(face['eyes']), 2)
        self.assertIn((288, 252), face['eyes'])
        self.assertIn((361, 251), face['eyes'])
        self.assertEqual(face['nose'], (325, 318))
        self.assertEqual(face['mouth'], (321, 338))

    def test_facial_landmarks_baby_face(self):
        _file = ImageFile(fetch_file('baby_face.jpg'))
        data = _file.analyze_facial_landmarks(with_landmarks=False)
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)

        face = data['dlib:Faces'][0]
        self.assertNotIn('eyes', face)
        self.assertNotIn('nose', face)
        self.assertNotIn('mouth', face)
        self.assertIn('position', face)

    def test_facial_landmarks_animated_image(self):
        _file = ImageFile(fetch_file('animated.gif'))
        data = _file.analyze_facial_landmarks()
        self.assertEqual(data, {})


class ImageFileBarcodeZXingTest(unittest.TestCase):

    def test_barcode_zxing_mona_lisa(self):
        _file = ImageFile(fetch_file('mona_lisa.jpg'))
        data = _file.analyze_barcode_zxing()
        self.assertEqual(data, {})

    def test_barcode_zxing_barcode(self):
        _file = ImageFile(fetch_file('barcode.png'))
        data = _file.analyze_barcode_zxing()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'CODABAR')
        self.assertEqual(data['zxing:Barcodes'][0]['data'], '137255')
        self.assertEqual(data['zxing:Barcodes'][0]['bounding box'],
                         {'width': 100, 'top': 29, 'height': 1, 'left': 4})

    def test_barcode_zxing_qrcode(self):
        _file = ImageFile(fetch_file('qrcode.jpg'))
        data = _file.analyze_barcode_zxing()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'QR_CODE')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'http://www.wikipedia.com')
        self.assertEqual(data['zxing:Barcodes'][0]['bounding box'],
                         {'width': 264, 'top': 52, 'height': 264, 'left': 50})

    def test_barcode_zxing_dmtx(self):
        _file = ImageFile(fetch_file('datamatrix.png'))
        data = _file.analyze_barcode_zxing()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'DATA_MATRIX')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'Wikipedia, the free encyclopedia')

    def test_barcode_zxing_multiple_barcodes(self):
        _file = ImageFile(fetch_file('multibarcodes.png'))
        data = _file.analyze_barcode_zxing()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 2)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'CODE_128')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         '2LUS94941+67000000')
        self.assertEqual(data['zxing:Barcodes'][1]['format'], 'ITF')
        self.assertEqual(data['zxing:Barcodes'][1]['data'], '054804124097')

    def test_barcode_zxing_small_files(self):
        _file = ImageFile(fetch_file('static.gif'))
        self.assertEqual(_file.analyze_barcode_zxing(), {})


@pytest.mark.timeout(60)
class ImageFileBarcodeZBarTest(unittest.TestCase):

    def test_barcode_zbar_mona_lisa(self):
        _file = ImageFile(fetch_file('mona_lisa.jpg'))
        data = _file.analyze_barcode_zbar()
        self.assertEqual(data, {})

    def test_barcode_zbar_vertical(self):
        _file = ImageFile(fetch_file('vertical_barcode.jpg'))
        data = _file.analyze_barcode_zbar()
        self.assertIn('zbar:Barcodes', data)
        self.assertEqual(len(data['zbar:Barcodes']), 2)
        self.assertEqual(data['zbar:Barcodes'][0]['format'], 'I25')
        self.assertEqual(data['zbar:Barcodes'][0]['data'],
                         '29430622992369')
        self.assertEqual(data['zbar:Barcodes'][1]['format'], 'I25')
        self.assertEqual(data['zbar:Barcodes'][1]['data'], '29322290481762')

    def test_barcode_zbar_qrcode(self):
        _file = ImageFile(fetch_file('qrcode.jpg'))
        data = _file.analyze_barcode_zbar()
        self.assertIn('zbar:Barcodes', data)
        self.assertEqual(len(data['zbar:Barcodes']), 1)
        self.assertEqual(data['zbar:Barcodes'][0]['format'], 'QRCODE')
        self.assertEqual(data['zbar:Barcodes'][0]['data'],
                         'http://www.wikipedia.com')
        self.assertEqual(data['zbar:Barcodes'][0]['bounding box'],
                         {'width': 350, 'top': 9, 'height': 350, 'left': 7})

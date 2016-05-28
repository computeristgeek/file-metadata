# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata._compat import PY2
from file_metadata.image.image_file import ImageFile
from tests import fetch_file, importable, mock, unittest


class ImageFileTest(unittest.TestCase):

    def setUp(self):
        self.ball_png = ImageFile(fetch_file('ball.png'))
        self.red_png = ImageFile(fetch_file('red.png'))
        self.green_png = ImageFile(fetch_file('green.png'))
        self.blue_png = ImageFile(fetch_file('blue.png'))

    def test_opencv_read(self):
        self.assertEqual(self.ball_png.opencv.shape, (226, 226, 3))

    @unittest.skipIf(not importable('pycolorname'),
                     "pycolorname not installed.")
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

    @mock.patch('{0}.__import__'.format('__builtin__' if PY2 else 'builtins'),
                side_effect=ImportError, autospec=True)
    def test_color_average_without_pycolorname(self, mocked_import):
        self.assertEqual(self.red_png.analyze_color_average(), {})
        self.assertEqual(mocked_import.call_count, 1)

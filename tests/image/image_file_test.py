# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from tests import fetch_file, unittest

from file_metadata.image.image_file import ImageFile


class ImageFileTest(unittest.TestCase):

    def setUp(self):
        self.ball_png = ImageFile(fetch_file('ball.png'))

    def test_opencv_read(self):
        self.assertEqual(self.ball_png.opencv.shape, (226, 226, 3))

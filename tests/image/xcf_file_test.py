# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import pytest

from file_metadata.image.xcf_file import XCFFile
from tests import fetch_file, unittest


class XCFFileTest(unittest.TestCase):

    def setUp(self):
        self.blank = XCFFile(fetch_file('blank.xcf'))
        self.woman = XCFFile(fetch_file('woman.xcf'))

    def test_fetch_filename_raster(self):
        self.assertTrue(self.blank.fetch('filename_raster').endswith('.png'))

    def test_fetch_ndarray(self):
        self.assertEqual(self.blank.fetch('ndarray').shape, (400, 640))
        self.assertEqual(self.woman.fetch('ndarray').shape, (1024, 720, 4))


# Increase the timeout as the first time it will need to download the
# shape predictor data ~60MB
@pytest.mark.timeout(300)
class XCFFileFaceLandmarksTest(unittest.TestCase):

    def setUp(self):
        self.blank = XCFFile(fetch_file('blank.xcf'))
        self.woman = XCFFile(fetch_file('woman.xcf'))

    def test_blank(self):
        data = self.blank.analyze_facial_landmarks()
        self.assertEqual(data, {})

    def test_facial_landmarks_woman_face(self):
        data = self.woman.analyze_facial_landmarks()
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)

        # The position varies by a few pixels depending on the version of
        # imagemagick as the conversion may blur the image more in older
        # versions. Hence, we don't check the position.

        # face = data['dlib:Faces'][0]
        # self.assertEqual(face['left_eye'], (277, 306))
        # self.assertEqual(face['right_eye'], (411, 292))
        # self.assertEqual(face['nose'], (359, 400))
        # self.assertEqual(face['mouth'], (356, 447))

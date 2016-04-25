# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import unittest

from file_metadata.utilities import make_temp


class MakeTempTest(unittest.TestCase):

    def test_make_temp_default(self):
        with make_temp() as testfile:
            testfilename = testfile
            self.assertTrue(os.path.isfile(testfile))
        self.assertFalse(os.path.exists(testfilename))

    def test_make_temp_kwargs(self):
        with make_temp(suffix=".orig", prefix="pre") as testfile:
            testfilename = testfile
            self.assertTrue(testfile.endswith(".orig"))
            self.assertTrue(os.path.basename(testfile).startswith("pre"))
        self.assertFalse(os.path.exists(testfilename))

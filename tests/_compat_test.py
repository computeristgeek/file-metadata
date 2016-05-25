# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import subprocess
import sys

from file_metadata._compat import check_output
from tests import unittest


class CheckOutputTest(unittest.TestCase):

    def test_stdout_valueerror(self):
        self.assertRaises(ValueError, check_output, ['echo', 'a'], stdout=1)

    def test_nonzero_exit(self):
        self.assertRaises(subprocess.CalledProcessError, check_output,
                          [sys.executable, '-c', 'unknown_func()'])

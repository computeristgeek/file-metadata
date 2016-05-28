# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import shutil
import subprocess
import sys
import tempfile

from file_metadata._compat import check_output, ffprobe_parser, makedirs
from tests import unittest


class CheckOutputTest(unittest.TestCase):

    def test_stdout_valueerror(self):
        self.assertRaises(ValueError, check_output, ['echo', 'a'], stdout=1)

    def test_nonzero_exit(self):
        self.assertRaises(subprocess.CalledProcessError, check_output,
                          [sys.executable, '-c', 'unknown_func()'])


class FFProbeParserTest(unittest.TestCase):
    def test_streams(self):
        data = ffprobe_parser("[STREAM]\n"
                              "index=0\n"
                              "[/STREAM]\n"
                              "[STREAM]\n"
                              "index=1\n"
                              "[/STREAM]")
        self.assertNotIn('format', data)
        self.assertIn('streams', data)
        self.assertEqual(len(data['streams']), 2)
        self.assertEqual(data['streams'][0]['index'], '0')
        self.assertEqual(data['streams'][1]['index'], '1')

    def test_stream(self):
        data = ffprobe_parser("[STREAM]\n"
                              "index=0\n"
                              "codec_time_base=0/1\n"
                              "codec_tag=0x0000\n"
                              "duration=10.833333\n"
                              "[/STREAM]")
        self.assertNotIn('format', data)
        self.assertIn('streams', data)
        self.assertEqual(len(data['streams']), 1)
        self.assertEqual(data['streams'][0]['index'], '0')
        self.assertEqual(data['streams'][0]['codec_tag'], '0x0000')
        self.assertEqual(data['streams'][0]['codec_time_base'], '0/1')
        self.assertEqual(data['streams'][0]['duration'], '10.833333')

    def test_format(self):
        data = ffprobe_parser("[FORMAT]\n"
                              "filename=path/to/file.ext\n"
                              "format_name=ogg\n"
                              "[/FORMAT]\n")
        self.assertNotIn('streams', data)
        self.assertIn('format', data)
        self.assertEqual(data['format']['filename'], 'path/to/file.ext')
        self.assertEqual(data['format']['format_name'], 'ogg')


class MakeDirsTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_makes_path(self):
        test_dirs = os.path.abspath(os.path.join(
            self.tempdir, 'make', 'these', 'dirs'))

        self.assertFalse(os.path.exists(test_dirs))
        self.assertEqual(makedirs(test_dirs), test_dirs)
        self.assertTrue(os.path.exists(test_dirs))

    def test_exist_ok(self):
        self.assertRaises(OSError, makedirs, self.tempdir)
        try:
            makedirs(self.tempdir, exist_ok=True)
        except OSError:
            self.fail('OSError was raised even though exist_ok=True')

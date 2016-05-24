# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.generic_file import GenericFile, magic
from tests import fetch_file, mock, unittest


class DerivedFile(GenericFile):

    def analyze(self):
        # Only use the `_analyze_test` functions for tests
        return GenericFile.analyze(self, prefix='analyze_test')

    def analyze_test1(self):
        return {"test1": "test1"}

    def analyze_test2(self):
        return {"test2": "test2"}


class DerivedFileTest(unittest.TestCase):

    def setUp(self):
        self.uut = DerivedFile(fetch_file('ascii.txt'))

    def test_metadata(self):
        self.assertEqual(self.uut.metadata, {'test1': 'test1',
                                             'test2': 'test2'})


class GenericFileTest(unittest.TestCase):

    def setUp(self):
        self.text_file = GenericFile(fetch_file('ascii.txt'))
        self.binary_file = GenericFile(fetch_file('file.bin'))
        self.wav_file = GenericFile(fetch_file('noise.wav'))

    def test_os_stat(self):
        data = self.text_file.analyze_os_stat()
        self.assertIn('File:FileSize', data)
        self.assertEqual(data['File:FileSize'], '98 bytes')

    @unittest.skipIf(not hasattr(magic, 'from_file'),
                     'python-magic from pypi not found.')
    def test_magic_mimetype(self):
        data = self.text_file.analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')
        data = self.wav_file.analyze_mimetype()
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')

    @unittest.skipIf(not hasattr(magic, 'open'),
                     'python-magic from `file` not found.')
    def test_file_magic_mimetype(self):
        data = self.text_file.analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')
        data = self.wav_file.analyze_mimetype()
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')

        data = self.wav_file.analyze_mimetype()
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')

    @mock.patch('file_metadata.generic_file.magic')
    def test_builtin_mimetype(self, mock_magic):
        del mock_magic.open
        del mock_magic.from_file

        data = self.text_file.analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')

        data = self.wav_file.analyze_mimetype()
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')

    def test_exiftool(self):
        data = self.binary_file.analyze_exiftool()
        self.assertTrue(data['File:FileSize'], '256 bytes')
        # The `exiftool` property should have all the info, but the
        # analyze method should not.
        self.assertNotIn('ExifTool:Error', data)
        self.assertIn('ExifTool:Error', self.binary_file.exiftool)

        data = self.text_file.analyze_exiftool()
        self.assertEqual(data['File:FileSize'], '98 bytes')

        data = self.wav_file.analyze_exiftool()
        self.assertEqual(data['File:FileSize'], '86 kB')

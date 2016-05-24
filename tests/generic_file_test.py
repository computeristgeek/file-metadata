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
        self.uut = GenericFile(fetch_file('ascii.txt'))

    def test_os_stat(self):
        data = self.uut.analyze_os_stat()
        self.assertIn('File:FileSize', data)
        self.assertEqual(data['File:FileSize'], '98 bytes')

    @unittest.skipIf(not hasattr(magic, 'from_file'),
                     'python-magic from pypi not found.')
    def test_magic_mimetype(self):
        data = self.uut.analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')
        data = self.wav_file.analyze_mimetype()
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')

    @unittest.skipIf(not hasattr(magic, 'open'),
                     'python-magic from `file` not found.')
    def test_file_magic_mimetype(self):
        data = self.uut.analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')
        data = self.wav_file.analyze_mimetype()
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')

    @mock.patch('file_metadata.generic_file.magic')
    def test_builtin_mimetype(self, mock_magic):
        del mock_magic.open
        del mock_magic.from_file
        data = self.uut.analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')

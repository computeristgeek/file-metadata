# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.generic_file import GenericFile, magic
from tests import fetch_file, mock, unittest, which_sideeffect


class DerivedFile(GenericFile):

    def analyze(self):  # Only use the `_analyze_test` functions for tests
        return GenericFile.analyze(self, prefix='analyze_test')

    def analyze_test1(self):
        return {"test1": "test1"}


class GenericFileTest(unittest.TestCase):

    def test_derived_file_analyze(self):
        uut = DerivedFile(fetch_file('ascii.txt'))
        self.assertEqual(uut.analyze(), {'test1': 'test1'})

    def test_config(self):
        uut = GenericFile(fetch_file('ascii.txt'), option1='one')
        self.assertEqual(uut.config('option1'), 'one')
        self.assertRaises(KeyError, uut.config, 'option2')

    def test_invalid_fetch(self):
        uut = GenericFile(fetch_file('ascii.txt'))
        self.assertEqual(uut.fetch('some_invalid_key'), None)

    def test_os_stat(self):
        data = GenericFile(fetch_file('ascii.txt')).analyze_os_stat()
        self.assertIn('File:FileSize', data)
        self.assertEqual(data['File:FileSize'], '98 bytes')

    @mock.patch('file_metadata.generic_file.magic')
    def test_magic_not_found(self, mock_magic):
        del mock_magic.open
        del mock_magic.from_file
        _file = GenericFile(fetch_file('ascii.txt'))
        self.assertRaises(ImportError, _file.analyze_mimetype)

    @mock.patch('file_metadata.generic_file.which',
                side_effect=which_sideeffect(['perl', 'exiftool']))
    def test_exiftool_not_found(self, mock_which):
        _file = GenericFile(fetch_file('ascii.txt'))
        self.assertRaises(OSError, _file.analyze_exifdata)


class GenericFileMagicTest(unittest.TestCase):
    __test__ = False

    def test_magic_text_plain(self):
        data = GenericFile(fetch_file('ascii.txt')).analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'text/plain')

    def test_magic_audio_wav(self):
        data = GenericFile(fetch_file('noise.wav')).analyze_mimetype()
        self.assertIn('File:MIMEType', data)
        self.assertEqual(data['File:MIMEType'], 'audio/x-wav')


@unittest.skipIf(not hasattr(magic, 'from_file'),
                 'python-magic from pypi not found.')
class GenericFilePypiMagicTest(GenericFileMagicTest):
    __test__ = True


@unittest.skipIf(not hasattr(magic, 'open'),
                 'python-magic from `file` not found.')
class GenericFilePkgMgrMagicTest(GenericFileMagicTest):
    __test__ = True


class GenericFileExiftoolTest(unittest.TestCase):
    __test__ = False

    def test_exiftool_binary(self, mock_which=None):
        data = self.binary_file.analyze_exifdata()
        self.assertTrue(data['File:FileSize'], '256 bytes')
        # The `exiftool` property should have all the info, but the
        # analyze method should not.
        self.assertNotIn('ExifTool:Error', data)
        self.assertIn('ExifTool:Error', self.binary_file.exiftool())

    def test_exiftool_text_plain(self, mock_which=None):
        data = self.text_file.analyze_exifdata()
        self.assertEqual(data['File:FileSize'], '98 bytes')

    def test_exiftool_audio_wav(self, mock_which=None):
        data = self.wav_file.analyze_exifdata()
        self.assertEqual(data['File:FileSize'], '86 kB')


class GenericFileDownloadedExiftoolTest(unittest.TestCase):
    __test__ = True


@mock.patch('file_metadata.generic_file.which',
            side_effect=which_sideeffect(['perl']))
class GenericFileInstalledExiftoolTest(unittest.TestCase):
    __test__ = True


class GenericFileCreateTest(unittest.TestCase):

    def test_create_image_file(self):
        from file_metadata.image.image_file import ImageFile
        for fname in ['red.png', 'example.tiff']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), ImageFile),
                'File "{0}" was not of type {1}'.format(fname, ImageFile))

    def test_create_jpeg_file(self):
        from file_metadata.image.jpeg_file import JPEGFile
        for fname in ['qrcode.jpg', 'cmyk.jpg', 'unknown_cmyk.jpg']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), JPEGFile),
                'File "{0}" was not of type {1}'.format(fname, JPEGFile))

    def test_create_xcf_file(self):
        from file_metadata.image.xcf_file import XCFFile
        for fname in ['blank.xcf']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), XCFFile),
                'File "{0}" was not of type {1}'.format(fname, XCFFile))

    def test_create_svg_file(self):
        from file_metadata.image.svg_file import SVGFile
        for fname in ['text_html.svg', 'text_plain.svg', 'image_svg_xml.svg',
                      'application_xml.svg']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), SVGFile),
                'File "{0}" was not of type {1}'.format(fname, SVGFile))

    def test_create_audio_file(self):
        from file_metadata.audio.audio_file import AudioFile
        for fname in ['drums.mid', 'bell.flac', 'bell.wav']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), AudioFile),
                'File "{0}" was not of type {1}'.format(fname, AudioFile))

    def test_create_generic_file(self):
        for fname in ['image.pdf', 'text.pdf']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), GenericFile),
                'File "{0}" was not of type {1}'.format(fname, GenericFile))

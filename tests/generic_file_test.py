# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import tempfile

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

    def test_file_close(self):
        uut = GenericFile(fetch_file('ascii.txt'))
        fd, name = tempfile.mkstemp(
            suffix=os.path.split(uut.fetch('filename'))[-1] + '.png')
        os.close(fd)
        uut.temp_filenames.add(name)
        self.assertTrue(os.path.exists(name))
        uut.close()
        self.assertFalse(os.path.exists(name))

    def test_enter_exit(self):
        name = None
        with GenericFile(fetch_file('ascii.txt')) as uut:
            fd, name = tempfile.mkstemp(
                suffix=os.path.split(uut.fetch('filename'))[-1] + '.png')
            os.close(fd)
            uut.temp_filenames.add(name)
            self.assertTrue(os.path.exists(name))
        self.assertFalse(os.path.exists(name))

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
                side_effect=which_sideeffect(['exiftool']))
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

    def test_exiftool_binary(self):
        _file = GenericFile(fetch_file('file.bin'))
        data = _file.analyze_exifdata()
        self.assertTrue(data['File:FileSize'], '256 bytes')
        # The `exiftool` property should have all the info, but the
        # analyze method should not.
        self.assertNotIn('ExifTool:Error', data)
        self.assertIn('ExifTool:Error', _file.exiftool())

    def test_exiftool_text_plain(self):
        data = GenericFile(fetch_file('ascii.txt')).analyze_exifdata()
        self.assertEqual(data['File:FileSize'], '98 bytes')

    def test_exiftool_audio_wav(self):
        data = GenericFile(fetch_file('noise.wav')).analyze_exifdata()
        self.assertEqual(data['File:FileSize'], '86 kB')

    def test_exiftool_encoding(self):
        _file = GenericFile(fetch_file('nonascii_exifdata.jpg'))
        # Test with a file that has non-ascii characters in the exif
        # information
        data = _file.analyze_exifdata()
        self.assertEqual(data['XMP:State'], 'Franche-Comté')
        self.assertIn('Éclipse', data['XMP:Description'])


class GenericFileCreateTest(unittest.TestCase):

    def test_create_enter_exit(self):
        name = None
        with GenericFile.create(fetch_file('ascii.txt')) as uut:
            fd, name = tempfile.mkstemp(
                suffix=os.path.split(uut.fetch('filename'))[-1] + '.png')
            os.close(fd)
            uut.temp_filenames.add(name)
            self.assertTrue(os.path.exists(name))
        self.assertFalse(os.path.exists(name))

    def test_create_image_file(self):
        from file_metadata.image.image_file import ImageFile
        for fname in ['red.png']:
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

    def test_create_tiff_file(self):
        from file_metadata.image.tiff_file import TIFFFile
        for fname in ['example.tiff']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), TIFFFile),
                'File "{0}" was not of type {1}'.format(fname, TIFFFile))

    def test_create_ogg_file(self):
        from file_metadata.audio.ogg_file import OGGFile
        for fname in ['bell.ogg', 'bell.oga']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), OGGFile),
                'File "{0}" was not of type {1}'.format(fname, OGGFile))

    def test_create_audio_file(self):
        from file_metadata.audio.audio_file import AudioFile
        for fname in ['drums.mid', 'bell.flac', 'bell.wav', 'bell.ogg',
                      'bell.oga']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), AudioFile),
                'File "{0}" was not of type {1}'.format(fname, AudioFile))

    def test_create_ogv_file(self):
        from file_metadata.video.ogv_file import OGVFile
        for fname in ['veins.ogv', 'ogg_video.ogg']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), OGVFile),
                'File "{0}" was not of type {1}'.format(fname, OGVFile))

    def test_create_video_file(self):
        from file_metadata.video.video_file import VideoFile
        for fname in ['sample.webm']:
            self.assertTrue(isinstance(
                GenericFile.create(fetch_file(fname)), VideoFile),
                'File "{0}" was not of type {1}'.format(fname, VideoFile))

    def test_create_application_file(self):
        from file_metadata.application.application_file import ApplicationFile
        for fname in ['image.pdf', 'text.pdf', 'empty.djvu']:
            self.assertTrue(isinstance(
                ApplicationFile.create(fetch_file(fname)), ApplicationFile),
                'File "{0}" was not of type {1}'.format(fname,
                                                        ApplicationFile))

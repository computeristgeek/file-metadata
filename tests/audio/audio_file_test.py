# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.audio.audio_file import AudioFile
from tests import fetch_file, unittest


class AudioFileCreateTest(unittest.TestCase):

    def test_create_audio_file(self):
        for fname in ['drums.mid', 'bell.flac', 'bell.wav']:
            self.assertTrue(isinstance(
                AudioFile.create(fetch_file(fname)), AudioFile),
                'File "{0}" was not of type audio'.format(fname))

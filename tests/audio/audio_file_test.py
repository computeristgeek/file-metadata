# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.audio.audio_file import AudioFile
from tests import fetch_file, unittest


class AudioFileTest(unittest.TestCase):

    def setUp(self):
        self.wikiexample_file = AudioFile(fetch_file('wikiexample.ogg'))
        self.wav_file = AudioFile(fetch_file('noise.wav'))
        self.bin_file = AudioFile(fetch_file('file.bin'))

    def test_audioread(self):
        data = self.wikiexample_file.analyze_audioread()
        self.assertEqual(data['AudioRead:SampleRate'], 44100)
        self.assertEqual(round(data['AudioRead:Duration']), 6)
        self.assertEqual(data['AudioRead:NumChannels'], 2)

        data = self.wav_file.analyze_audioread()
        self.assertEqual(data['AudioRead:SampleRate'], 44100)
        self.assertEqual(data['AudioRead:Duration'], 1)
        self.assertEqual(data['AudioRead:NumChannels'], 1)

        data = self.bin_file.analyze_audioread()
        self.assertEqual(data, {})

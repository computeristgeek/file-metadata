# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from whichcraft import which

from file_metadata.mixins import FFProbeMixin
from tests import fetch_file, mock, unittest


def which_sideeffect(unavailable_executables):
    def wrapper(command, *args, **kwargs):
        if command in unavailable_executables:
            return None
        return which(command, *args, **kwargs)
    return wrapper


class FFProbeMixinTest(unittest.TestCase):
    __test__ = False

    def setUp(self):
        self.wikiexample_file = FFProbeMixin()
        self.wikiexample_file.filename = fetch_file('wikiexample.ogg')
        self.wav_file = FFProbeMixin()
        self.wav_file.filename = fetch_file('noise.wav')
        self.veins_file = FFProbeMixin()
        self.veins_file.filename = fetch_file('veins.ogv')
        self.bin_file = FFProbeMixin()
        self.bin_file.filename = fetch_file('file.bin')

    def test_bin(self, mock_check_output):
        data = self.bin_file.analyze_ffprobe()
        self.assertEqual(data, {})

    def test_ogg(self, mock_check_output):
        data = self.wikiexample_file.analyze_ffprobe()
        self.assertIn('FFProbe:Format', data)
        self.assertEqual(data['FFProbe:Format'], 'ogg')
        self.assertEqual(round(data['FFProbe:Duration']), 6)
        self.assertEqual(data['FFProbe:NumStreams'], 1)

        stream = data['FFProbe:Streams'][0]
        self.assertEqual(stream['Format'], 'audio/vorbis')
        self.assertNotIn('Width', stream)
        self.assertNotIn('Height', stream)
        self.assertEqual(stream['Rate'], '2/-/44100')
        self.assertEqual(round(stream['Duration']), 6)

    def test_wav(self, mock_check_output):
        data = self.wav_file.analyze_ffprobe()
        self.assertIn('FFProbe:Format', data)
        self.assertEqual(data['FFProbe:Format'], 'wav')
        self.assertEqual(data['FFProbe:Duration'], 1)
        self.assertEqual(data['FFProbe:NumStreams'], 1)

        stream = data['FFProbe:Streams'][0]
        self.assertEqual(stream['Format'], 'audio/pcm_s16le')
        self.assertNotIn('Width', stream)
        self.assertNotIn('Height', stream)
        self.assertEqual(stream['Rate'], '1/-/44100')
        self.assertEqual(round(stream['Duration']), 1)

    def test_ogv(self, mock_check_output):
        data = self.veins_file.analyze_ffprobe()
        self.assertIn('FFProbe:Format', data)
        self.assertEqual(data['FFProbe:Format'], 'ogg')
        self.assertEqual(round(data['FFProbe:Duration']), 11)
        self.assertEqual(data['FFProbe:NumStreams'], 2)

        stream = data['FFProbe:Streams'][0]
        self.assertEqual(stream['Format'], 'data/unknown')
        self.assertNotIn('Width', stream)
        self.assertNotIn('Height', stream)
        self.assertNotIn('Rate', stream)

        stream = data['FFProbe:Streams'][1]
        self.assertEqual(stream['Format'], 'video/theora')
        self.assertEqual(stream['Width'], 320)
        self.assertEqual(stream['Height'], 240)
        self.assertEqual(round(stream['Duration']), 11)


@unittest.skipIf(which('ffprobe') is None, '`ffprobe` not found.')
@mock.patch('file_metadata.mixins.which',
            side_effect=which_sideeffect(['avprobe']))
class FFProbeMixinWithFFProbeTest(FFProbeMixinTest):
    __test__ = True


@unittest.skipIf(which('avprobe') is None, '`avprobe` not found.')
@mock.patch('file_metadata.mixins.which',
            side_effect=which_sideeffect(['ffprobe']))
class FFProbeMixinWithAVProbeTest(FFProbeMixinTest):
    __test__ = True


@mock.patch('file_metadata.mixins.which',
            side_effect=which_sideeffect(['ffprobe', 'avprobe']))
class FFProbeMixinWithoutBackendsTest(unittest.TestCase):
    def setUp(self):
        self.wav_file = FFProbeMixin()
        self.wav_file.filename = fetch_file('noise.wav')

    def test_wav(self, mock_check_output):
        self.assertRaises(OSError, self.wav_file.analyze_ffprobe)

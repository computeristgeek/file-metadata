# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata._compat import which
from file_metadata.generic_file import GenericFile
from file_metadata.mixins import is_svg, FFProbeMixin
from tests import fetch_file, mock, unittest, which_sideeffect


class FFProbeTestFile(GenericFile, FFProbeMixin):
    pass


class FFProbeMixinTest(unittest.TestCase):
    __test__ = False

    def test_bin(self, mock_which):
        _file = FFProbeTestFile(fetch_file('file.bin'))
        data = _file.analyze_ffprobe()
        self.assertEqual(data, {})

    def test_multiline_value(self, mock_with):
        _file = FFProbeTestFile(fetch_file('multiline_ffprobe.ogg'))
        data = _file.analyze_ffprobe()
        self.assertIn('FFProbe:Format', data)
        self.assertEqual(data['FFProbe:Format'], 'ogg')
        self.assertEqual(int(data['FFProbe:Duration']), 224)
        self.assertEqual(data['FFProbe:NumStreams'], 1)

        stream = data['FFProbe:Streams'][0]
        self.assertEqual(stream['Format'], 'audio/vorbis')
        self.assertNotIn('Width', stream)
        self.assertNotIn('Height', stream)
        self.assertIn('44100', stream['Rate'])
        self.assertEqual(int(stream['Duration']), 224)

    def test_ogg(self, mock_which):
        _file = FFProbeTestFile(fetch_file('wikiexample.ogg'))
        data = _file.analyze_ffprobe()
        self.assertIn('FFProbe:Format', data)
        self.assertEqual(data['FFProbe:Format'], 'ogg')
        self.assertEqual(round(data['FFProbe:Duration']), 6)
        self.assertEqual(data['FFProbe:NumStreams'], 1)

        stream = data['FFProbe:Streams'][0]
        self.assertEqual(stream['Format'], 'audio/vorbis')
        self.assertNotIn('Width', stream)
        self.assertNotIn('Height', stream)
        self.assertIn('44100', stream['Rate'])
        self.assertEqual(round(stream['Duration']), 6)

    def test_wav(self, mock_which):
        _file = FFProbeTestFile(fetch_file('noise.wav'))
        data = _file.analyze_ffprobe()
        self.assertIn('FFProbe:Format', data)
        self.assertEqual(data['FFProbe:Format'], 'wav')
        self.assertEqual(data['FFProbe:Duration'], 1)
        self.assertEqual(data['FFProbe:NumStreams'], 1)

        stream = data['FFProbe:Streams'][0]
        self.assertEqual(stream['Format'], 'audio/pcm_s16le')
        self.assertNotIn('Width', stream)
        self.assertNotIn('Height', stream)
        self.assertIn('44100', stream['Rate'])
        self.assertEqual(round(stream['Duration']), 1)

    def test_ogv(self, mock_which):
        _file = FFProbeTestFile(fetch_file('veins.ogv'))
        data = _file.analyze_ffprobe()
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
    def test_wav(self, mock_check_output, mock_system=None):
        _file = FFProbeTestFile(fetch_file('noise.wav'))
        self.assertRaises(OSError, _file.analyze_ffprobe)


class IsSvgTest(unittest.TestCase):

    def test_is_svg_application_xml(self):
        _file = GenericFile(fetch_file('application_xml.svg'))
        self.assertTrue(is_svg(_file))

    def test_is_svg_image_svg_xml(self):
        _file = GenericFile(fetch_file('image_svg_xml.svg'))
        self.assertTrue(is_svg(_file))

    def test_is_svg_text_plain(self):
        _file = GenericFile(fetch_file('text_plain.svg'))
        self.assertTrue(is_svg(_file))

    def test_is_svg_text_html(self):
        _file = GenericFile(fetch_file('text_html.svg'))
        self.assertTrue(is_svg(_file))

    def test_is_svg_binary(self):
        _file = GenericFile(fetch_file('file.bin'))
        self.assertFalse(is_svg(_file))

    def test_is_svg_png(self):
        _file = GenericFile(fetch_file('red.png'))
        self.assertFalse(is_svg(_file))

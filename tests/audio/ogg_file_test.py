# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.audio.ogg_file import OGGFile
from tests import fetch_file, unittest


class OGGFileTest(unittest.TestCase):

    def test_file_format(self):
        for filename in ['bell.oga', 'bell.ogg']:
            with OGGFile(fetch_file(filename)) as uut:
                data = uut.analyze_file_format()
                self.assertIn('Composite:FileFormat', data)
                self.assertEqual(data['Composite:FileFormat'], 'ogg')

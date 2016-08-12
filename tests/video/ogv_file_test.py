# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.video.ogv_file import OGVFile
from tests import fetch_file, unittest


class OGVFileTest(unittest.TestCase):

    def test_file_format(self):
        for filename in ['veins.ogv', 'ogg_video.ogg']:
            with OGVFile(fetch_file(filename)) as uut:
                data = uut.analyze_file_format()
                self.assertIn('Composite:FileFormat', data)
                self.assertEqual(data['Composite:FileFormat'], 'ogv')

# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import tempfile

import wand.image

from file_metadata.image.image_file import ImageFile
from file_metadata.utilities import memoized


class SVGFile(ImageFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @memoized
    def fetch(self, key=''):
        if key == 'filename_raster':
            # SVG files are not raster graphics, hence we convert it to one
            # and use that instead.
            with wand.image.Image(filename=self.fetch('filename')) \
                    as svg_image:
                svg_image.format = 'png'
                fd, name = tempfile.mkstemp(
                    suffix=os.path.split(self.fetch('filename'))[-1] + '.png',
                    prefix='tmp_file_metadata')
                os.close(fd)
                svg_image.save(filename=name)
                self.temp_filenames.add(name)
                return name

        return super(SVGFile, self).fetch(key)

    def analyze_file_format(self):
        """
        Simply add a metadata mentioning this is a valid SVG file. This is
        useful because SVG cannot be simply detected by MimeType as it's not
        standardized yet.

        :return: dict with the keys:

             - Composite:FileFormat - 'svg'
        """
        return {'Composite:FileFormat': 'svg'}

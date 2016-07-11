# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import tempfile

import pathlib2
import wand.image

from file_metadata.image.image_file import ImageFile
from file_metadata.utilities import memoized


class TIFFFile(ImageFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @memoized
    def fetch(self, key=''):
        if key == 'filename_zxing':
            pill = self.fetch('pillow')
            if hasattr(pill, 'n_frames') and pill.n_frames != 1:
                return None
            # ZXing cannot handle most TIFF images, convert to PNG.
            with wand.image.Image(filename=self.fetch('filename')) \
                    as tiff_image:
                tiff_image.format = 'png'
                fd, name = tempfile.mkstemp(
                    suffix=os.path.split(self.fetch('filename'))[-1] + '.png',
                    prefix='tmp_file_metadata')
                os.close(fd)
                tiff_image.save(filename=name)
                self.temp_filenames.add(name)
                return pathlib2.Path(name).as_uri()

        return super(TIFFFile, self).fetch(key)

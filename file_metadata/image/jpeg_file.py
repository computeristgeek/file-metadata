# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import tempfile

import pathlib2
import skimage.io

from file_metadata.image.image_file import ImageFile
from file_metadata.utilities import memoized


class JPEGFile(ImageFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @memoized
    def fetch(self, key=''):
        if key == 'filename_zxing':
            exif = self.exiftool()
            if (exif.get('APP14:ColorTransform') == 'Unknown (RGB or CMYK)' or
                    exif.get('ICC_Profile:ColorSpaceData') == 'CMYK' or
                    exif.get('XMP:ColorMode') == 'CMYK'):
                # ZXing cannot handle CMYK encoded JPEG images. Write the RGB
                # data to a tempfile and use that.
                fd, name = tempfile.mkstemp(
                    suffix=os.path.split(self.fetch('filename'))[-1],
                    prefix='tmp_file_metadata')
                os.close(fd)
                skimage.io.imsave(name, self.fetch('ndarray'))
                self.temp_filenames.add(name)
                return pathlib2.Path(name).as_uri()

        return super(JPEGFile, self).fetch(key)

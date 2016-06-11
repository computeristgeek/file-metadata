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

    @memoized(is_method=True)
    def fetch(self, key=''):
        if key == 'filename_zxing':
            exif = self.analyze_exifdata()
            if (exif.get('ICC_Profile:ColorSpaceData', None) == 'CMYK' or
                    exif.get('XMP:ColorMode', None) == 'CMYK'):
                # ZXing cannot handle CMYK encoded JPEG images. Write the RGB
                # data to a tempfile and use that.
                fd, name = tempfile.mkstemp(
                    suffix=os.path.split(self.fetch('filename'))[-1],
                    prefix='tmp_file_metadata')
                os.close(fd)
                skimage.io.imsave(name, self.fetch('ndarray'))
                return pathlib2.Path(name).as_uri()

        return super(JPEGFile, self).fetch(key)

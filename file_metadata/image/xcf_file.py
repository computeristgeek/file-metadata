# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import tempfile

import wand.image

from file_metadata.image.image_file import ImageFile
from file_metadata.utilities import memoized


class XCFFile(ImageFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @memoized
    def fetch(self, key=''):
        if key == 'filename_raster':
            # XCF files are not raste graphics, hence we convert it to one
            # and use that instead.
            with wand.image.Image(filename=self.fetch('filename')) \
                    as xcf_image:
                xcf_image.format = 'png'
                fd, name = tempfile.mkstemp(
                    suffix=os.path.split(self.fetch('filename'))[-1] + '.png',
                    prefix='tmp_file_metadata')
                os.close(fd)
                xcf_image.save(filename=name)
                self.temp_filenames.add(name)
                return name

        return super(XCFFile, self).fetch(key)

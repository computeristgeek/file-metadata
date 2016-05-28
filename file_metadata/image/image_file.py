# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import cv2

from file_metadata.generic_file import GenericFile
from file_metadata.utilities import PropertyCached


class ImageFile(GenericFile):
    mimetypes = ()

    @PropertyCached
    def opencv(self):
        return cv2.imread(self.filename)

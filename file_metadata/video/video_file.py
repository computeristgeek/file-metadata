# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.generic_file import GenericFile
from file_metadata.mixins import FFProbeMixin


class VideoFile(FFProbeMixin, GenericFile):
    mimetypes = ()

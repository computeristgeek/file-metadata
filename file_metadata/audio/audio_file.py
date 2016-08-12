# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.generic_file import GenericFile
from file_metadata.mixins import FFProbeMixin


class AudioFile(FFProbeMixin, GenericFile):
    mimetypes = ()

    @classmethod
    def create(cls, *args, **kwargs):
        cls_file = cls(*args, **kwargs)
        if cls_file.is_type('ogg'):
            from file_metadata.audio.ogg_file import OGGFile
            return OGGFile.create(*args, **kwargs)
        return cls(*args, **kwargs)

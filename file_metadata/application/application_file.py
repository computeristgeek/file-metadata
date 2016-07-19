# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.generic_file import GenericFile


class ApplicationFile(GenericFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

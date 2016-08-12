# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.audio.audio_file import AudioFile


class OGGFile(AudioFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def analyze_file_format(self):
        """
        Simply add a metadata mentioning this is a valid OGG file. This is
        useful because OGG cannot be simply detected by MimeType as it shares
        the same mime with OGV.

        :return: dict with the keys:

             - Composite:FileFormat - 'ogg'
        """
        return {'Composite:FileFormat': 'ogg'}

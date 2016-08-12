# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.video.video_file import VideoFile


class OGVFile(VideoFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def analyze_file_format(self):
        """
        Simply add a metadata mentioning this is a valid OGV file. This is
        useful because OGV cannot be simply detected by MimeType as it shares
        the same mime with OGG.

        :return: dict with the keys:

             - Composite:FileFormat - 'ogv'
        """
        return {'Composite:FileFormat': 'ogv'}

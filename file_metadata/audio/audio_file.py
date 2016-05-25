# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import audioread

from file_metadata.generic_file import GenericFile
from file_metadata.mixins import FFProbeMixin


class AudioFile(FFProbeMixin, GenericFile):
    mimetypes = ()

    def analyze_audioread(self):
        try:
            with audioread.audio_open(self.filename) as f:
                return {
                    'AudioRead:Duration': f.duration,
                    'AudioRead:SampleRate': f.samplerate,
                    'AudioRead:NumChannels': f.channels}
        except audioread.NoBackendError, audioread.DecodeError:
            return {}

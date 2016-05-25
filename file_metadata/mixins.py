# -*- coding: utf-8 -*-
"""
Mixins to add functionalities to some File classes. Meant for analysis
methods which are not completely generic, but can be used for multiple
formats.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import json
import os
import subprocess

from file_metadata.utilities import DictNoNone, PropertyCached
from file_metadata._compat import check_output, JSONDecodeError


class FFProbeMixin:

    @PropertyCached
    def ffprobe(self):
        """
        Read multimedia streams and give information about it using the
        ffmpeg utility ffprobe (or avprobe from libav-tools, a fork of
        ffmpeg).
        """
        probe_args = ('-v', '0', '-show_format', '-show_streams',
                      os.path.abspath(self.filename), '-of', 'json')
        try:
            proc = check_output(('ffprobe',) + probe_args)
        except subprocess.CalledProcessError as proc_error:  # pragma: no cover
            output = proc_error.output.decode('utf-8').rstrip('\r\n')
        except OSError:
            # Use avprobe if ffprobe not found
            try:
                proc = check_output(('avprobe',) + probe_args)
            except subprocess.CalledProcessError \
                    as proc_error:
                output = proc_error.output.decode('utf-8').rstrip('\r\n')
            except OSError:
                return {}
            else:
                output = proc.decode('utf-8').rstrip('\r\n')
        else:
            output = proc.decode('utf-8').rstrip('\r\n')

        try:
            data = json.loads(output)
        except JSONDecodeError:  # pragma: no cover
            return {}

        return data

    def analyze_ffprobe(self):
        """
        Use ``ffprobe`` and return streams and format from it.

        :return: dict containing all the data from ``ffprobe``.
        """
        if not self.ffprobe:
            return {}

        def fmt(key):
            return self.ffprobe['format'].get(key, None)

        data = DictNoNone({
            'FFProbe:Format': fmt('format_name'),
            'FFProbe:Duration': float(fmt('duration')),
            'FFProbe:NumStreams': fmt('nb_streams')})

        streams = []
        for stream in self.ffprobe['streams']:
            def strm(key, default=None):
                return stream.get(key, default)

            rate = width = height = None
            if strm("codec_type") == "video":
                rate = strm("avg_frame_rate")
                width, height = int(strm("width")), int(strm("height"))
            elif strm("codec_type") == "audio":
                rate = '%s/%s/%s' % (strm("channels", '-'),
                                     strm("sample_fmt", '-'),
                                     int(float(strm("sample_rate", '-'))))

            streams.append(DictNoNone({
                'Format': '{0}/{1}'.format(strm('codec_type'),
                                           strm('codec_name')),
                'Width': width,
                'Height': height,
                # 'Channels': strm('channels'),
                # 'SampleRate': strm('sample_rate'),
                # 'AvgFrameRate': (None if strm('avg_frame_rate') == '0/0'
                #                  else strm('avg_frame_rate')),
                'Rate': rate,
                'Duration': (None if strm('duration').lower() == 'n/a'
                             else float(strm('duration')))}))

        data['FFProbe:Streams'] = streams or None
        return data

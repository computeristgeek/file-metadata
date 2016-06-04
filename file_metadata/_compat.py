# -*- coding: utf-8 -*-
"""
Provides utilities to handle the python2 and python3 differences.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import re


def ffprobe_parser(output):
    """
    Parse output from the older versions of avprode/ffprobe. The -of or
    -print_format argument was added in versions 0.9+. This allows json
    output. But in older versions like 0.8.17 which is used in ubuntu
    precise, json output is not possible. In such cases, this function
    can be used to parse the output.

    :param output: The INI like syntax from ffprobe.
    :return:       The parsed dict.
    """
    streams = re.findall('\[STREAM\](.*?)\[\/STREAM\]', output, re.S)
    _format = re.findall('\[FORMAT\](.*?)\[\/FORMAT\]', output, re.S)

    def parse_section(section):
        section_dict = {}
        for line in section.strip().splitlines():
            key, val = line.strip().split("=", 1)
            section_dict[key.strip()] = val.strip()
        return section_dict

    data = {}
    if streams:
        parsed_streams = [parse_section(stream) for stream in streams]
        data['streams'] = parsed_streams
    if _format:
        parsed_format = parse_section(_format[0])
        data['format'] = parsed_format
    return data


def makedirs(name, exist_ok=False, **kwargs):
    """
    Make the directories in the given path.  The ``exist_ok`` argument was
    added in python 3.2+.
    """
    if not (exist_ok and os.path.exists(name)):
        os.makedirs(name, **kwargs)
    return name

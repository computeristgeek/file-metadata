# -*- coding: utf-8 -*-
"""
Provides utilities to handle the python2 and python3 differences.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import json
import os
import re
import subprocess
import sys

try:  # Python 3
    from urllib.request import urlopen  # flake8: noqa (unused import)
except ImportError:  # Python 2
    from urllib2 import urlopen  # flake8: noqa (unused import)

try:  # pragma: no cover
    JSONDecodeError = json.decoder.JSONDecodeError
except AttributeError:  # pragma: no cover
    JSONDecodeError = ValueError

PY2 = sys.version_info[0] == 2


def check_output(*popenargs, **kwargs):
    """
    Run command with arguments and return its output.

    If the exit code was non-zero it raises a CalledProcessError. The
    CalledProcessError object will have the returncode and output attributes.
    The arguments are the same as for the Popen constructor.  Example::

    >>> check_output(["echo", "hello world"]).strip()
    'hello world'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use ``stderr=subprocess.STDOUT``::

    >>> check_output(["non_existent_file"], stderr=subprocess.STDOUT)
    Traceback (most recent call last):
        ...
    OSError: [Errno 2] No such file or directory
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        exc = subprocess.CalledProcessError(retcode,
                                            kwargs.get("args", popenargs[0]))
        exc.output = output  # output attrib not there in python2.6
        raise exc
    return output


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

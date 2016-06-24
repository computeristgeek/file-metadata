# -*- coding: utf-8 -*-
"""
Provides utilities to handle the python2 and python3 differences.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import re
import sys


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


try:
    from shutil import which
except ImportError:
    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        """
        Given a command, mode, and a PATH string, return the path which
        conforms to the given mode on the PATH, or None if there is no such
        file.
        `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
        of os.environ.get("PATH"), or can be overridden with a custom search
        path.
        """
        # Check that a given file can be accessed with the correct mode.
        # Additionally check that `file` is not a directory, as on Windows
        # directories pass the os.access check.
        def _access_check(fn, mode):
            return (os.path.exists(fn) and os.access(fn, mode) and
                    not os.path.isdir(fn))

        # If we're given a path with a directory part, look it up directly.
        if os.path.dirname(cmd):
            return cmd if _access_check(cmd, mode) else None

        path = path if path is not None else os.environ.get("PATH", os.defpath)
        if not path:
            return None

        path = path.split(os.pathsep)
        if sys.platform == "win32":
            # The current directory takes precedence on Windows.
            if os.curdir not in path:
                path.insert(0, os.curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
            # See if the given file matches any of the expected path
            # extensions. This will allow us to short circuit when given
            # "python.exe". If it does match, only test that one, otherwise we
            # have to try others.
            if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
                files = [cmd]
            else:
                files = [cmd + ext for ext in pathext]
        else:
            # On other platforms you don't have things like PATHEXT to tell you
            # what file suffixes are executable, so just pass on cmd as-is.
            files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if normdir not in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None

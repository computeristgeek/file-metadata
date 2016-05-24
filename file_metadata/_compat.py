# -*- coding: utf-8 -*-
"""
Provides utilities to handle the python2 and python3 differences.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import json
import subprocess

try:  # Python 3
    from urllib.request import urlopen  # flake8: noqa (unused import)
except ImportError:  # Python 2
    from urllib2 import urlopen  # flake8: noqa (unused import)

try:  # pragma: no cover
    JSONDecodeError = json.decoder.JSONDecodeError
except AttributeError:  # pragma: no cover
    JSONDecodeError = ValueError


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

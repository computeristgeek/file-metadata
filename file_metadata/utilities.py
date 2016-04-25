# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
    print_function)

import os
import sys
import tempfile
from shutil import copyfileobj

try:
    from urllib.request import urlopen  # Python 3
except ImportError:
    from urllib2 import urlopen  # Python 2

from contextlib import contextmanager


PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


def download(url, filename, overwrite=False):
    """
    Download the given URL to the given filename. If the file exists, it won't
    be downloaded.

    :param url:       A URL to download.
    :param filename:  The file to store the downloaded file to.
    :param overwrite: Set to True if the file should be downloaded even if it
                      already exists.
    :return:          The filename.
    """
    if not exists(filename) or overwrite:
        with urlopen(url) as response, open(filename, 'wb') as out_file:
            copyfileobj(response, out_file)

    return filename


@contextmanager
def make_temp(suffix="", prefix="tmp", dir=None):
    """
    Create a temporary file with a closed stream and deletes it when done.

    :return: A contextmanager retrieving the file path.
    """
    temporary = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(temporary[0])
    try:
        yield temporary[1]
    finally:
        os.remove(temporary[1])

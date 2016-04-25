# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
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
    Download the given URL to the given filename. If the file exists,
    it won't be downloaded unless asked to overwrite. Both, text data
    like html, txt, etc. or binary data like images, audio, etc. are
    acceptable.

    :param url:       A URL to download.
    :param filename:  The file to store the downloaded file to.
    :param overwrite: Set to True if the file should be downloaded even if it
                      already exists.
    """
    if not os.path.exists(filename) or overwrite:
        response = urlopen(url)
        with open(filename, 'wb') as out_file:
            copyfileobj(response, out_file)


@contextmanager
def make_temp(suffix="", prefix="tmp", directory=None):
    """
    Create a temporary file with a closed stream and deletes it when done.

    >>> with make_temp() as testfile:
    ...     testfilename = testfile
    ...     print("Inside `with`:", os.path.isfile(testfile))
    ...
    Inside `with`: True
    >>> print("Outside `with`:", os.path.exists(testfile))
    ...
    Outside `with`: False

    And even force the file to have a specific properties:
    >>> with make_temp(suffix='.test', prefix='test_') as testfile:
    ...     print('Prefix:', os.path.basename(testfile)[:5])
    ...     print('Suffix:', os.path.basename(testfile)[-5:])
    ...     os.remove(testfile)  # No clean up does if file already deleted
    ...
    Prefix: test_
    Suffix: .test

    :param suffix:
        A string to add to the end of the tempfile name.
    :param suffix:
        A string to add to the start of the tempfile name.
    :param directory:
        The directory to put the tempfile in. By default it uses the
        system's temporary folder.
    :return:
        A contextmanager retrieving the file path.
    """
    fd, name = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
    os.close(fd)
    try:
        yield name
    finally:
        if os.path.exists(name):
            os.remove(name)

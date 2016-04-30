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


class PropertyCached(object):
    """
    A decorator than is similar to the ``property`` decorator but saves
    the return value into the property when called the first time.

    Makes properties that simply have a hidden variable much simpler to
    handle. For example:

    >>> class OldMethod:
    ...     @property
    ...     def answer(self):
    ...         if not hasattr(self, '_answer'):
    ...             print("Computing the answer ...")
    ...             self._answer = 42
    ...         return self._answer
    ...
    >>> old = OldMethod()
    >>> old.answer
    Computing the answer ...
    42
    >>> old.answer
    42

    Can now be changed to

    >>> class NewMethod:
    ...     @PropertyCached
    ...     def answer(self):
    ...         print("Computing the answer ...")
    ...         return 42
    ...
    >>> new = NewMethod()
    >>> new.answer
    Computing the answer ...
    42
    >>> new.answer
    42

    To delete the cached value, simply do:

    >>> del new.__dict__['answer']
    >>> new.answer
    Computing the answer ...
    42
    """

    def __init__(self, wrapped_function):
        self.wrapped_function = wrapped_function

    def __get__(self, instance, _type=None):
        retval = self.wrapped_function(instance)
        instance.__dict__[self.wrapped_function.__name__] = retval
        return retval

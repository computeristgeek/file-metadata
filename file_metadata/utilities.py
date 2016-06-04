# -*- coding: utf-8 -*-
"""
A bunch of utility functions that help out with basic functionality in
python. Provides utilities to handle common tasks and boilerplate code.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import bz2
import hashlib
import os
import tarfile
import tempfile
from shutil import copyfileobj

try:
    import lzma
except ImportError:
    from backports import lzma

import appdirs
from six.moves.urllib.request import urlopen

from file_metadata._compat import makedirs
from contextlib import contextmanager


PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


def to_cstr(value):
    """
    Convert a python string into a C style string. Meant for packages which
    expect C strings like boost.python and other python bindings on C
    libraries.
    C strings are 8 byte ansii. Hence, we convert the unicode from python to
    that format.

    >>> to_cstr(u'a')
    'a'
    """
    return value.encode('utf-8')


def download(url, filename, overwrite=False, timeout=None):
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
        if timeout is None:
            response = urlopen(url)
        else:
            response = urlopen(url, timeout=timeout)
        with open(filename, 'wb') as out_file:
            copyfileobj(response, out_file)


def bz2_decompress(filepath, newfilepath, block_size=64 * 1024):
    """
    Decompress the given file using a bz2 decompressor.

    :param filepath:    The filepath of the archived file.
    :param newfilepath: The path to decompress the file into.
    :param block_size:  The block size to iteratively decompress with.
    """
    with open(newfilepath, 'wb') as new_file:
        _file = bz2.BZ2File(filepath, 'rb')
        for data in iter(lambda: _file.read(block_size), ''):
            new_file.write(data)
        _file.close()


def targz_decompress(filepath, newfilepath):
    """
    Decompress the given file using a tar+gz decompressor.

    :param filepath:    The filepath of the archived file.
    :param newfilepath: The path to decompress the file into.
    """
    tar = tarfile.open(filepath, "r:gz")
    tar.extractall(newfilepath)
    tar.close()


def tarxz_decompress(filepath, newfilepath):
    """
    Decompress the given file using a tar+xz decompressor.

    :param filepath:    The filepath of the archived file.
    :param newfilepath: The path to decompress the file into.
    """
    with lzma.open(filepath) as lzma_file:
        tar = tarfile.open(fileobj=lzma_file)
        tar.extractall(newfilepath)
        tar.close()


def md5sum(filename, blocksize=64 * 1024):
    """
    Take a file and find it's md5sum.

    :param filepath:  The filepath to find md5sum of.
    :param blocksize: The block size to iteratively read with.
    """
    _hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            _hash.update(block)
    return _hash.hexdigest()


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


class DictNoNone(dict):
    """
    Create a dict but don't set the item if a value is ``None``.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for key, val in self.items():
            if val is None:
                del self[key]

    def __setitem__(self, key, value):
        if key in self or value is not None:
            dict.__setitem__(self, key, value)


def app_dir(dirtype, *args):
    """
    The path to store all module data into. It auto created the directory if
    it doesn't exist. It does not create any of the paths given in ``args``.

    :param args: The args to append to the data directory.
    """
    if dirtype not in ('user_config_dir', 'user_data_dir', 'user_log_dir',
                       'user_cache_dir', 'site_config_dir', 'site_data_dir'):
        return None
    path = os.path.abspath(getattr(appdirs, dirtype)('file-metadata'))
    return os.path.join(makedirs(path, exist_ok=True), *args)

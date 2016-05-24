# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import random
import string
import struct
import wave

try:  # Python 2
    import unittest2 as unittest
except ImportError:
    import unittest

try:  # Python 3
    import unittest.mock as mock  # flake8: noqa (unused import)
except ImportError:  # Python 2
    import mock  # flake8: noqa (unused import)


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'files')


def fetch_file(name, overwrite=False):
    """
    Fetch a file based on the given key. If the file is not found, it is
    created appropriately by either generating it or downloading it from
    elsewhere.

    :param name:      The name (key) of the file that is needed.
    :param overwrite: Force overwrite if file exists.
    :return:          The absolute path of the requested file.
    """
    filepath = os.path.join(CACHE_DIR, name)

    if not os.path.isdir(CACHE_DIR):  # Make folder is it doesn't exist
        os.makedirs(CACHE_DIR)

    if os.path.exists(filepath) and not overwrite:  # Use cached file
        return filepath

    # Miscellaneous files
    if name == 'ascii.txt':
        with open(filepath, 'w') as file_handler:
            file_handler.writelines([
                string.ascii_lowercase, '\n', string.ascii_uppercase, '\n',
                string.digits, '\n', string.punctuation, '\n'])
    # Music files
    elif name == "noise.wav":
        wav_file = wave.open(filepath, 'w')
        wav_file.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
        for _ in range(44100):  # 1 second
            value = struct.pack('h', random.randint(-32767, 32767))
            wav_file.writeframes(value)
        wav_file.close()
    else:
        raise ValueError('Asked to fetch unknown file.')

    return filepath

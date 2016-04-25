# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import tempfile

from contextlib import contextmanager


PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


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

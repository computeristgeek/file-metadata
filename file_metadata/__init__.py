# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os

from file_metadata.utilities import PROJECT_PATH


with open(os.path.join(PROJECT_PATH, "VERSION")) as fp:
    __version__ = fp.read().strip()

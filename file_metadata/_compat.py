# -*- coding: utf-8 -*-
"""
Provides utilities to handle the python2 and python3 differences.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

try:  # Python 3
    from urllib.request import urlopen  # flake8: noqa (unused import)
except ImportError:  # Python 2
    from urllib2 import urlopen  # flake8: noqa (unused import)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import subprocess
import sys

from setuptools import find_packages, setup


# Check if exiftool is installed.
try:
    out = subprocess.check_output(['exiftool', '-ver'])
    if int(out.split(".", 1)[0]) < 8:
        print('`exiftool` (http://www.sno.phy.queensu.ca/~phil/exiftool/) '
              'version found was less than 8.0. Please update it.')
except (OSError, subprocess.CalledProcessError):
    print('`exiftool` (http://www.sno.phy.queensu.ca/~phil/exiftool/) needs '
          'to be installed and needs to be made available in your PATH.')
    sys.exit(1)

# Check if opencv is installed.
try:
    import cv2  # flake8: noqa (unused import)
except ImportError:
    print("`OpenCV` (http://opencv.org/) or it's python bindings are not "
          "installed or not in your python PATH.")
    sys.exit(1)

# Check if java is installed.
try:
    out = subprocess.check_output(['java', '-version'])
except (OSError, subprocess.CalledProcessError):
    print('`java` (https://java.com/) needs to be installed and needs to '
          'be made available in your PATH.')
    sys.exit(1)

# Make a list of required packages
required = open('requirements.txt').read().strip().splitlines()

test_required = open('test-requirements.txt').read().strip().splitlines()
VERSION = open(os.path.join('file_metadata', 'VERSION')).read().strip()

if __name__ == "__main__":
    setup(name='file-metadata',
          version=VERSION,
          description='Helps to find structured metadata from a given file.',
          author="DrTrigon",
          author_email="dr.trigon@surfeu.ch",
          maintainer="AbdealiJK",
          maintainer_email='abdealikothari@gmail.com',
          url='https://github.com/AbdealiJK/file-metadata',
          platforms='any',
          packages=find_packages(exclude=["build.*", "tests.*", "tests"]),
          install_requires=required,
          tests_require=test_required,
          license="MIT",
          # Setuptools has a bug where they use isinstance(x, str) instead
          # of basestring. Because of this we convert it to str.
          package_data={str('file_metadata'): [str("VERSION")]},
          # from http://pypi.python.org/pypi?%3Aaction=list_classifiers
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Environment :: MacOS X',
              'Environment :: Win32 (MS Windows)',
              'Intended Audience :: Developers',
              'Operating System :: OS Independent',
              'Programming Language :: Python :: Implementation :: CPython'])

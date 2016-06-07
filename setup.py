#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import platform
import subprocess
import sys

from setuptools import find_packages, setup


with open(os.devnull, 'w') as nul:
    # Check if exiftool or perl is installed.
    try:
        out = subprocess.check_call(['perl', '-v'], stdout=nul, stderr=nul)
    except (OSError, subprocess.CalledProcessError):
        try:
            out = subprocess.check_call(['exiftool', '-ver'], stdout=nul,
                                        stderr=nul)
        except (OSError, subprocess.CalledProcessError):
            print('`perl` (https://www.perl.org/) or `exiftool` '
                  '(http://www.sno.phy.queensu.ca/~phil/exiftool/) '
                  'need to be installed and made available in your PATH. '
                  'On Ubuntu, you can install perl with '
                  '`sudo apt-get install perl` or install exiftool with '
                  '`sudo apt-get install exiftool`.')
            sys.exit(1)

    # Check if java is installed.
    try:
        out = subprocess.check_call(['java', '-version'], stdout=nul,
                                    stderr=nul)
    except (OSError, subprocess.CalledProcessError):
        print('`java` (https://java.com/) needs to be installed and needs to '
              'be made available in your PATH. If using Ubuntu, you can do '
              '`sudo apt-get install openjdk-7-jre`')
        sys.exit(1)

    # Check if avprobe of ffprobe is installed if system is not Linux.
    # If it's linux, we use static builds from http://johnvansickle.com/libav/
    if platform.system() != 'Linux':
        try:
            out = subprocess.check_call(['ffprobe', '-version'], stdout=nul,
                                        stderr=nul)
        except (OSError, subprocess.CalledProcessError):
            try:
                out = subprocess.check_output(['avprobe', '-version'],
                                              stdout=nul, stderr=nul)
            except (OSError, subprocess.CalledProcessError):
                print('`ffprobe` (https://ffmpeg.org/ffprobe.html) or '
                      '`avprobe` (http://libav.org/documentation/avprobe.html)'
                      'need to be installed and made available in your PATH. '
                      'If using Ubuntu, you can install avprobe with '
                      '`sudo apt-get install libav-tools`.')
            sys.exit(1)


def read_reqs(reqs_filename):
    reqs = open(reqs_filename).read().strip().splitlines()
    return list(i for i in reqs if not (i.startswith('#') or len(i) == 0))

required = read_reqs('requirements.txt')
test_required = read_reqs('test-requirements.txt')
VERSION = open(os.path.join('file_metadata', 'VERSION')).read().strip()

if sys.version_info >= (3,):
    # mock is not required for python 3
    test_required.remove('mock')

if __name__ == "__main__":
    setup(name='file-metadata',
          version=VERSION,
          description='Helps to find structured metadata from a given file.',
          author="DrTrigon",
          author_email="dr.trigon@surfeu.ch",
          maintainer="AbdealiJK",
          maintainer_email='abdealikothari@gmail.com',
          url='https://github.com/AbdealiJK/file-metadata',
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

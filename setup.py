#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from setuptools import find_packages, setup

import file_metadata

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

with open('test-requirements.txt') as requirements:
    test_required = requirements.read().splitlines()

if __name__ == "__main__":
    setup(name='file-metadata',
          version=file_metadata.__version__,
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

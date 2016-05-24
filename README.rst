Introduction
============

``file-metadata`` is a python package that aims to analyze files and find
metadata that can be used from it.

Installation
============

The easiest way to install the library is using ``pip``. To install the
latest stable version run:

::

    $ pip install file-metadata

To get bightly builds from the master branch of the github repo, use:

::

    $ pip install --pre file-metadata

Usage
=====

The package is still under heavy development and is not usable right now.

Development
===========

Testing
-------

To test the code, install dependencies using:

::

    $ pip install -r test-requirements.txt

and then execute:

::

    $ python -m pytest

Build status
------------

.. image:: https://travis-ci.org/AbdealiJK/file-metadata.svg?branch=master
   :target: https://travis-ci.org/AbdealiJK/file-metadata

Credits
-------

This package has been derived from
`pywikibot-compat <https://gerrit.wikimedia.org/r/#/admin/projects/pywikibot/compat>`__.
Specifically, the script ``catimages.py`` which can be found at
`pywikibot-compat/catimages.py <https://phabricator.wikimedia.org/diffusion/PWBO/browse/master/catimages.py>`__.
These packages were created by `DrTrigon <mailto:dr.trigon@surfeu.ch>`__ who
is the original author of this package.

LICENSE
=======

.. image:: https://img.shields.io/github/license/AbdealiJK/file-metadata.svg
   :target: https://opensource.org/licenses/MIT

This code falls under the
`MIT License <https://tldrlegal.com/license/mit-license>`__.
Please note that some files or content may be copied from other places
and have their own licenses. Dependencies that are being used to generate
the databases also have their own licenses.

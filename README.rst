Introduction
============

``file-metadata`` is a python package that aims to analyze files and find
metadata that can be used from it.

Installation
============

The easiest way to install the library is using ``pip``. To install the
latest stable version run::

    $ pip install file-metadata

To get nightly builds from the master branch of the github repo, use::

    $ pip install --pre file-metadata

Note that there are 3 dependencies which need to be manually installed:

-  `exiftool <http://www.sno.phy.queensu.ca/~phil/exiftool/>`__
-  `opencv <http://opencv.org/>`__ - v2.x is supported, although v3.x should
   also work.
-  `java <https://java.com/en/>`__

Usage
=====

To use the package, you first need a file which can be any media file.

Let us first download an example qrcode from commons wikimedia::

    $ wget https://upload.wikimedia.org/wikipedia/commons/5/5b/Qrcode_wikipedia.jpg -O qrcode.jpg

And now, let us create a File object from this::

    >>> from file_metadata.generic_file import GenericFile
    >>> qr = GenericFile.create('qrcode.jpg')

Notice that when creating the file, the class automatically finds the best
type of class to analyze the file. In this case, it auto detecs that the
file is an image file, and uses the ``ImageFile`` class::

    >>> qr.__class__.__name__
    'ImageFile'

Now, to find possible analysis routines supported for the file, ``help(qr)``
can be checked. All routines beginning with ``analyze_`` perform analysis.
As the example we have is a qrcode, let us use ``analyze_barcode()``::

    >>> qr.analyze_barcode()
    {'zxing:Barcodes': [{'data': 'http://www.wikipedia.com',
       'format': 'QR_CODE',
       'points': [(50.0, 316.0), (50.0, 52.0), (314.0, 52.0), (278.0, 280.0)],
       'raw_data': 'http://www.wikipedia.com'}]}

Which tells us the bounding box of the barcode (``points``) and also the data
(``http://www.wikipedia.com``). It also mentions that the format of the barcode
is QR_CODE.

Similarly, to check the mimetype, the analysis routing ``analyze_mimetype()``
can be used::

    >>> qr.analyze_mimetype()
    {'File:MIMEType': 'image/jpeg'}

To perform all the analyze routines on the image, the
``analyze()`` method can be used. It runs all the analysis routines on the
file and gives back the merged result::

    >>> qr.analyze()
 
Development
===========

Testing
-------

To test the code, install dependencies using::

    $ pip install -r test-requirements.txt

and then execute::

    $ python -m pytest

Build status
------------

.. image:: https://travis-ci.org/AbdealiJK/file-metadata.svg?branch=master
   :target: https://travis-ci.org/AbdealiJK/file-metadata

.. image:: https://codecov.io/gh/AbdealiJK/file-metadata/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/AbdealiJK/file-metadata

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

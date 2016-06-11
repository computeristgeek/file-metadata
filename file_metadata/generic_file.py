# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import json
import logging
import os
import subprocess

import magic
from whichcraft import which

from file_metadata.mixins import is_svg
from file_metadata.utilities import (memoized, app_dir,
                                     download, targz_decompress)


class GenericFile(object):
    """
    Object corresponding to a single file. An abstract class that can be
    used for any mimetype/media-type (depending of the file itself). Provides
    helper functions to open files, and analyze basic data common to all
    types of files.

    Any class that inherits from this abstract class would probably want to
    set the ``mimetypes`` and override the ``analyze()`` or write their
    own ``analyze_*()`` methods depending on the file type and analysis
    routines that should be run.

    :ivar mimetypes: Set of mimetypes (strings) applicable to this class
        based on the official standard by IANA.
    """
    mimetypes = ()
    NO_CONFIG = object()

    def __init__(self, fname, **kwargs):
        self.filename = fname
        self.options = kwargs

    def config(self, key):
        defaults = {}
        return self.options.get(key, defaults[key])

    @memoized(is_method=True)
    def fetch(self, key=''):
        """
        Fetch data about the file based on the key provided. Provides a
        uniform location where all the conversions of filetype, reading, etc.
        can happen efficiently and also it gets cached as it's memoized.

        :param key: The key decides what data is fetched.
        """
        if key == '' or key == 'filename':
            return os.path.abspath(self.filename)
        return None

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Create an object which best suits the given file. It first opens the
        file as a GenericFile and then uses the mimetype analysis to suggest
        the best class to use.

        :param args:   The args to pass to the file class.
        :parak kwargs: The kwargs to pass to the file class.
        :return:       A class inheriting from GenericFile.
        """
        cls_file = cls(*args, **kwargs)
        mime = cls_file.analyze_mimetype()['File:MIMEType']
        _type, subtype = mime.split('/', 1)

        if (_type == 'image' or mime == 'application/x-xcf' or
                is_svg(cls_file)):
            from file_metadata.image.image_file import ImageFile
            return ImageFile.create(*args, **kwargs)
        elif _type == 'audio':
            from file_metadata.audio.audio_file import AudioFile
            return AudioFile.create(*args, **kwargs)
        elif _type == 'video':
            from file_metadata.video.video_file import VideoFile
            return VideoFile.create(*args, **kwargs)

        return cls_file

    def analyze(self, prefix='analyze_', suffix='', methods=None):
        """
        Analyze the given file and create metadata information appropriately.
        Search and use all methods that have a name starting with
        ``analyze_*`` and merge the doctionaries using ``.update()``
        to get the cumulative set of metadata.

        :param prefix:  Use only methods that have this prefix.
        :param suffix:  Use only methods that have this suffix.
        :param methods: A list of method names to choose from. If not given,
                        a sorted list of all methods from the class is used.
        :return: A dict containing the cumulative metadata.
        """
        data = {}
        methods = methods or sorted(dir(self))
        for method in methods:
            if method.startswith(prefix) and method.endswith(suffix):
                data.update(getattr(self, method)())
        return data

    @memoized(is_method=True)
    def exiftool(self):
        """
        The exif data from the given file using ``exiftool``. The data it
        fetches includes:

         - Basic file information
         - Exif data
         - XMP data
         - ICC Profile data
         - Composite data
         - GIMP, Adobe, Inkscape specific file data
         - Vorbis data for audio files
         - JFIF data
         - SVG data

        and many more types of information. For more information see
        <http://www.sno.phy.queensu.ca/~phil/exiftool/>.

        :return:      A dictionary containing the exif information.
        """
        if which('perl') is not None:
            folder = 'Image-ExifTool-10.15'
            arch = folder + '.tar.gz'
            arch_path = app_dir('user_data_dir', arch)
            bin_path = app_dir('user_data_dir', folder, 'exiftool')

            if not os.path.exists(bin_path):
                logging.info('Downloading `exiftool` to analyze exif data. '
                             'Hence, the first run may take longer than '
                             'normal.')
                url = 'http://www.sno.phy.queensu.ca/~phil/exiftool/' + arch
                download(url, arch_path)
                targz_decompress(arch_path, app_dir('user_data_dir'))
            executable = ('perl', bin_path)
        elif which('exiftool') is not None:
            executable = ('exiftool',)
        else:
            raise OSError('Neither perl nor exiftool were found.')

        command = executable + ('-G', '-j',
                                os.path.abspath(self.fetch('filename')))
        try:
            proc = subprocess.check_output(command)
        except subprocess.CalledProcessError as proc_error:
            output = proc_error.output.decode('utf-8').rstrip('\r\n')
        else:
            output = proc.decode('utf-8').rstrip('\r\n')

        data = json.loads(output)

        assert len(data) == 1
        return data[0]

    def analyze_os_stat(self):
        """
        Use the python ``os`` library to find file-system related metadata.

        :return: dict with the keys:

                  - File:FileSize - The size of the file in bytes.
        """
        stat_data = os.stat(self.fetch('filename'))
        return {"File:FileSize": str(stat_data.st_size) + " bytes"}

    def analyze_mimetype(self):
        """
        Use libmagic to identify the mimetype of the file. This analysis is
        done using multiple methods. The list (in priority order) is:

         - python-magic pypi library.
         - python-magic provided by ``file`` utility (Not supported, but
           provided for better compatibility with system packages).
         - Python's builtin ``mimetypes`` module.

        :return: dict with the keys:

                 - File:MIMEType - The IANA mimetype string for this file.
        """
        if hasattr(magic, "from_file"):
            # Use https://pypi.python.org/pypi/python-magic
            mime = magic.from_file(self.fetch('filename'), mime=True)
        elif hasattr(magic, "open"):
            # Use the python-magic library in distro repos from the `file`
            # command - http://www.darwinsys.com/file/
            magic_instance = magic.open(magic.MAGIC_MIME)
            magic_instance.load()
            mime = magic_instance.file(self.fetch('filename'))
        else:
            raise ImportError('The `magic` module that was found is not the '
                              'expected pypi package python-magic '
                              '(https://pypi.python.org/pypi/python-magic) '
                              'nor file\'s (http://www.darwinsys.com/file/) '
                              'package.')
        return {"File:MIMEType": mime}

    def analyze_exifdata(self, ignored_keys=()):
        """
        Use ``exiftool`` and return metadata from it.

        :return: dict containing all the data from ``exiftool``. It also
                 uses the groups given by exiftool.
        """
        # We remove unimportant data as this is an analysis routine for the
        # file. The method `exiftool` continues to have all the data.
        ignored_keys = set(ignored_keys + (
            'SourceFile', 'ExifTool:ExifToolVersion', 'ExifTool:Error',
            'ExifTool:Warning' 'File:FileName', 'File:Directory',
            'File:MIMEType'))
        return dict((key, val) for key, val in self.exiftool().items()
                    if key not in ignored_keys)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import mimetypes
import os

try:
    import magic
except ImportError as error:
    magic = error


class GenericFile:
    """
    Object corresponding to a single file. An abstract class that can be
    used for any mimetype/media-type (depending of the file itself). Provides
    helper functions to open files, and read basic data common to all
    types of files.

    Any class that inherits from this abstract class would probably want to
    override the ``analyze()`` and ``read_file()`` functions depending on
    the file type and analysis routine that should be run.

    :ivar mimetypes: Set of mimetypes (strings) applicable to this class
        based on the official standard by IANA.
    """
    mimetypes = ()

    def __init__(self, fname):
        self.filename = fname

    def analyze(self):
        """
        Analyze the given file and create metadata information appropriately.
        Uses all class methods that have a name starting with ``_analyze_*``
        and merges the doctionaries to get the final cumulative set of metadata.
        """
        self._metadata = {}
        for analysis_method in dir(self):
            if not analysis_method.startswith("_analyze_"):
                continue
            self._metadata.update(getattr(self, analysis_method)())

    def read_file(self):
        """
        Read the file using the class member ``filename`` and return the
        contents in an appropriate data-type (depending on the file itself).
        
        :return: The contents of the file associated to the object instance.
        """
        return None

    @property
    def metadata(self):
        """
        A python dictionary of all the metadata identified by analyzing
        the given file. This property is read-only and cannot be modified.
        """
        if not hasattr(self, "_metadata"):
            self.analyze()
        return self._metadata

    @property
    def file(self):
        """
        The file's contents of the file associated to an object instance.
        This property is read-only and cannot be modified, it uses the
        member function ``read_file()`` to read the file if it has not been
        read yet.
        """
        if not hasattr(self, "_file"):
            self._file = self.read_file()
        return self._file
    
    def flush(self):
        """
        Flush all information about the file. Useful when the file is modified
        and the file needs to be read and analyzed again.
        """
        delattr(self, "_file")
        delattr(self, "_metadata")

    def _analyze_os_stat(self):
        stat_data = os.stat(self.filename)
        return {"Size of file": str(stat_data.st_size) + " bytes"}

    def _analyze_mimetype(self):
        if hasattr(magic, "open"):
            # Use the python-magic library in distro repos from the `file`
            # command - http://www.darwinsys.com/file/
            magic_instance = magic.open( magic.MAGIC_MIME )
            magic_instance.load()
            mime = magic_instance.file(self.filename)
        elif hasattr(magic, "from_file"):
            # Use https://pypi.python.org/pypi/python-magic
            mime = magic.from_file(self.filename, mime=True)
        else:
            # Silently use python's builtin mimetype handler if magic package
            # was not found or not supported.
            mime, encoding = mimetypes.guess_type(self.filename)
        return {"MIME type": mime}

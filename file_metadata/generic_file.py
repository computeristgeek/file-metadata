# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.utilities import PropertyCached


class GenericFile:
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

    def __init__(self, fname):
        self.filename = fname

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

    @PropertyCached
    def metadata(self):
        """
        A python dictionary of all the metadata identified by analyzing
        the given file. This property is read-only and cannot be modified.

        :return: All the metadata found about the given file.
        """
        return self.analyze()

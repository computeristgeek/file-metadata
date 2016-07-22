# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.generic_file import GenericFile


class ApplicationFile(GenericFile):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def analyze_softwares(self):
        """
        Find the software used to create the given file with. It uses the exif
        data to find the softare that was used to create the file. It gives out
        a curated a list of softwares.

        :return: dict with the keys:

             - Composite:Softwares - Tuple with the names of the softwares
                detected that have been used with this file.
                The possible softwares that can be found are:
                    doPDF, LibreOffice, ACDSee, iText
        """
        exif = self.exiftool()
        data = {}

        softwares = set()

        for sw_key in ('PDF:Producer',):
            sw = str(exif.get(sw_key, '')).lower()
            if sw.startswith('libreoffice') or sw.startswith('libre office'):
                if exif.get('PDF:Creator', '').lower() == 'impress':
                    softwares.add('LibreOffice Impress')
                else:
                    softwares.add('LibreOffice')
            elif sw.startswith('dopdf'):
                softwares.add('doPDF')
            elif sw.startswith('acdsee'):
                softwares.add('ACDSee')
            elif sw.startswith('iText'):
                softwares.add('iText')

        if len(softwares) > 0:
            data['Composite:Softwares'] = tuple(softwares)
        return data

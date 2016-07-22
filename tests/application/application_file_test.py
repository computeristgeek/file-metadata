# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from file_metadata.application.application_file import ApplicationFile
from tests import fetch_file, unittest


class ApplicationFileSoftwaresTest(unittest.TestCase):

    def test_pdf_software_libreoffice(self):
        with ApplicationFile(fetch_file('created_with_libreoffice.pdf')) \
                as _file:
            data = _file.analyze_softwares()
            self.assertIn('Composite:Softwares', data)
            self.assertIn('LibreOffice Impress', data['Composite:Softwares'])

    # def test_pdf_software_dopdf(self):
    #     with ApplicationFile(fetch_file('created_with_dopdf.pdf')) as _file:
    #         data = _file.analyze_softwares()
    #         self.assertIn('Composite:Softwares', data)
    #         self.assertEqual(data['Composite:Softwares'], 'doPDF')

    # def test_pdf_software_acdsee(self):
    #     with ApplicationFile(fetch_file('created_with_acdsee.pdf')) as _file:
    #         data = _file.analyze_softwares()
    #         self.assertIn('Composite:Softwares', data)
    #         self.assertEqual(data['Composite:Softwares'], 'ACDSee')

    # def test_pdf_software_itext(self):
    #     with ApplicationFile(fetch_file('created_with_itext.pdf')) as _file:
    #         data = _file.analyze_softwares()
    #         self.assertIn('Composite:Softwares', data)
    #         self.assertEqual(data['Composite:Softwares'], 'iText')

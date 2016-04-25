# -*- coding: utf-8 -*-

from PIL import Image

from file_metadata.generic_file import GenericFile

class JPEGFile(GenericFile):
    mimetypes = ('image/jpeg', 'image/pjpeg')

    def read_file(self):
        return Image.open(self.filename)

    def _analyze_basic_info(self):
        data = {}
        data["Image Height"] = self.file.height
        data["Image Width"] = self.file.width

        if "dpi" in self.file.info:
            data["Dots Per Inches"] = self.file.info["dpi"]

        return data

    # def _analyze_exif(self):
    #     exif_data = {
    #         PIL.ExifTags.TAGS[k]: v
    #         for k, v in i._getexif().items()
    #         if k in PIL.ExifTags.TAGS
    #     }
    #     return exif_data

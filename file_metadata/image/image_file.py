# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import cv2

from file_metadata.generic_file import GenericFile
from file_metadata.utilities import PropertyCached


class ImageFile(GenericFile):
    mimetypes = ()

    @PropertyCached
    def opencv(self):
        return cv2.imread(self.filename)

    def analyze_color_average(self):
        """
        Find the average RGB color of the image and compare with the existing
        Pantone color system to identify the color name.
        """
        try:
            from pycolorname.pantone.pantonepaint import PantonePaint
        except ImportError:
            return {}

        mean_color = cv2.mean(self.opencv)[:3][::-1]
        # cv2.mean Assumes 4 channels and uses the color format BGR
        closest_label, closest_color = PantonePaint().find_closest(mean_color)

        return {
            'Color:ClosestLabeledColorRGB': closest_color,
            'Color:ClosestLabeledColor': closest_label,
            'Color:AverageRGB': tuple(round(i, 3) for i in mean_color)}

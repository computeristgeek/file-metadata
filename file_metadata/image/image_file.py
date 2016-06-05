# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import logging
import os
import re
import subprocess

import dlib
import pathlib2
import skimage.io
from pycolorname.pantone.pantonepaint import PantonePaint

from file_metadata._compat import makedirs
from file_metadata.generic_file import GenericFile
from file_metadata.utilities import (app_dir, bz2_decompress, download,
                                     to_cstr, memoize)


class ImageFile(GenericFile):
    mimetypes = ()

    @classmethod
    def create(cls, *args, **kwargs):
        cls_file = cls(*args, **kwargs)
        mime = cls_file.analyze_mimetype()['File:MIMEType']
        if mime == 'image/jpeg':
            from file_metadata.image.jpeg_file import JPEGFile
            return JPEGFile.create(*args, **kwargs)
        return cls(*args, **kwargs)

    @memoize
    def fetch(self, key=''):
        if key == 'filename_zxing':
            return pathlib2.Path(self.fetch('filename')).as_uri()
        elif key == 'ndarray':
            return skimage.io.imread(self.fetch('filename'))
        return super(ImageFile, self).fetch(key)

    def analyze_color_average(self):
        """
        Find the average RGB color of the image and compare with the existing
        Pantone color system to identify the color name.
        """
        image_array = self.fetch('ndarray')
        if len(image_array.shape) == 4:  # Animated images
            mean_color = image_array.mean(axis=(0, 1, 2))
        elif len(image_array.shape) == 3:  # Static images
            mean_color = image_array.mean(axis=(0, 1))
        elif len(image_array.shape) == 2:  # Greyscale images
            avg = image_array.mean()
            mean_color = (avg, avg, avg)

        mean_color = mean_color[:3]  # Remove alpha channel if existent
        closest_label, closest_color = PantonePaint().find_closest(mean_color)

        return {
            'Color:ClosestLabeledColorRGB': closest_color,
            'Color:ClosestLabeledColor': closest_label,
            'Color:AverageRGB': tuple(round(i, 3) for i in mean_color)}

    def analyze_facial_landmarks(self,
                                 with_landmarks=True,
                                 detector_upsample_num_times=0):
        """
        Use ``dlib`` to find the facial landmarks and also detect pose.

        Note: It works only for frontal faces, not for profile faces, etc.

        :param detector_upsample_num_times:
            The number of times to upscale the image by when detecting faces.
        """
        image_array = self.fetch('ndarray')
        if image_array.shape == 4:
            logging.warn('Facial landmarks of animated images cannot be '
                         'detected yet.')
            return {}

        predictor_dat = 'shape_predictor_68_face_landmarks.dat'
        predictor_arch = predictor_dat + '.bz2'
        dat_path = app_dir('user_data_dir', predictor_dat)
        arch_path = app_dir('user_data_dir', predictor_arch)

        if with_landmarks and not os.path.exists(dat_path):
            logging.info('Downloading the landmark data file for facial '
                         'landmark detection. Hence, the '
                         'first run may take longer than normal.')
            url = 'http://sourceforge.net/projects/dclib/files/dlib/v18.10/{0}'
            download(url.format(predictor_arch), arch_path)
            bz2_decompress(arch_path, dat_path)

        detector = dlib.get_frontal_face_detector()

        # TODO: Get orientation data from ``orient_id`` and use it.
        faces, scores, orient_id = detector.run(
            image_array,
            upsample_num_times=detector_upsample_num_times)

        if len(faces) == 0:
            return {}

        if with_landmarks:
            predictor = dlib.shape_predictor(to_cstr(dat_path))

        data = []
        for face, score in zip(faces, scores):
            fdata = {
                'position': {'left': face.left(),
                             'top': face.top(),
                             'right': face.right(),
                             'bottom': face.bottom()},
                'score': score}

            # dlib's shape detector uses the ibug dataset to detect shape.
            # More info at: http://ibug.doc.ic.ac.uk/resources/300-W/
            if with_landmarks:
                shape = predictor(image_array, face)

                def tup(point):
                    return point.x, point.y

                def tup2(pt1, pt2):
                    return int((pt1.x + pt2.x) / 2), int((pt1.y + pt2.y) / 2)

                # Point 34 is the tip of the nose
                fdata['nose'] = tup(shape.part(34))
                # Point 40 and 37 are the two corners of the left eye
                fdata['left_eye'] = tup2(shape.part(40), shape.part(37))
                # Point 46 and 43 are the two corners of the right eye
                fdata['right_eye'] = tup2(shape.part(46), shape.part(43))
                # Point 49 and 55 are the two outer corners of the mouth
                fdata['mouth'] = tup2(shape.part(49), shape.part(55))
            data.append(fdata)

        return {'dlib:Faces': data}

    def analyze_barcode(self):
        """
        Use ``zxing`` tot find barcodes, qr codes, data matrices, etc.
        from the image.
        """
        # Make directory for data
        path_data = app_dir('user_data_dir', 'zxing')
        makedirs(path_data, exist_ok=True)

        def download_jar(path, name, ver):
            logging.info('Downloading the zxing jar file to analyze barcodes. '
                         'Hence, the first run may take longer '
                         'than normal.')
            data = {'name': name, 'ver': ver, 'path': path}
            fname = os.path.join(path_data, '{name}-{ver}.jar'.format(**data))
            download('http://central.maven.org/maven2/{path}/{name}/{ver}/'
                     '{name}-{ver}.jar'.format(**data),
                     fname)
            return fname

        # Download all important jar files
        path_core = download_jar('com/google/zxing', 'core', '3.2.1')
        path_javase = download_jar('com/google/zxing', 'javase', '3.2.1')
        path_jcomm = download_jar('com/beust', 'jcommander', '1.48')

        output = subprocess.check_output([
            'java', '-cp', ':'.join([path_core, path_javase, path_jcomm]),
            'com.google.zxing.client.j2se.CommandLineRunner', '--multi',
            self.fetch('filename_zxing')])

        if 'No barcode found' in output:
            return {}

        barcodes = []
        for section in output.split("\nfile:"):
            lines = section.strip().splitlines()

            _format = re.search(r'format:\s([^,]+)', lines[0]).group(1)
            raw_result = lines[2]
            parsed_result = lines[4]
            num_pts = int(re.search(r'Found (\d+) result points.', lines[5])
                          .group(1))
            points = []
            float_re = r'(\d*[.])?\d+'
            for i in range(num_pts):
                pt = re.search(r'\(\s*{0}\s*,\s*{0}\s*\)'.format(float_re),
                               lines[6 + i])
                point = float(pt.group(1)), float(pt.group(2))
                points.append(point)
            barcodes.append({'format': _format, 'points': points,
                             'raw_data': raw_result, 'data': parsed_result})

        return {'zxing:Barcodes': barcodes}

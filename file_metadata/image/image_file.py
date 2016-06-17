# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import logging
import os
import re
import subprocess
import warnings

import dlib
import numpy
import pathlib2
import skimage
import skimage.io
import skimage.color
import skimage.transform
import zbar
from PIL import Image
from pycolorname.pantone.pantonepaint import PantonePaint

from file_metadata._compat import makedirs
from file_metadata.generic_file import GenericFile
from file_metadata.utilities import (app_dir, bz2_decompress, download,
                                     to_cstr, memoized)

# A Decompression Bomb is a small compressed image file which when decompressed
# uses a uge amount of RAM. For example, a monochrome PNG file with 100kx100k
# pixels. This tells PIL to make this warning into an error.
warnings.simplefilter('error', Image.DecompressionBombWarning)


class ImageFile(GenericFile):
    mimetypes = ()

    def config(self, key, new_defaults=()):
        defaults = {
            "max_decompressed_size": int(1024 ** 3 / 4 / 3)  # In bytes
        }
        defaults.update(dict(new_defaults))  # Update the defaults from child
        return super(ImageFile, self).config(key, new_defaults=defaults)

    @classmethod
    def create(cls, *args, **kwargs):
        cls_file = cls(*args, **kwargs)
        mime = cls_file.mime()
        _type, subtype = mime.split('/', 1)

        if mime == 'image/jpeg':
            from file_metadata.image.jpeg_file import JPEGFile
            return JPEGFile.create(*args, **kwargs)
        elif _type in ('image', 'application') and subtype == 'x-xcf':
            from file_metadata.image.xcf_file import XCFFile
            return XCFFile.create(*args, **kwargs)
        elif cls_file.is_type('svg'):
            from file_metadata.image.svg_file import SVGFile
            return SVGFile.create(*args, **kwargs)
        return cls(*args, **kwargs)

    @memoized(is_method=True)
    def fetch(self, key=''):
        if key == 'filename_raster':
            # A raster filename holds the file in a raster graphic format
            return self.fetch('filename')
        elif key == 'filename_zxing':
            return pathlib2.Path(self.fetch('filename_raster')).as_uri()
        elif key == 'ndarray':
            Image.MAX_IMAGE_PIXELS = self.config('max_decompressed_size')
            try:
                image_array = skimage.io.imread(self.fetch('filename_raster'))
                if image_array.shape == (2,):
                    # Assume this is related to
                    # https://github.com/scikit-image/scikit-image/issues/2154
                    return image_array[0]
                return image_array
            except Image.DecompressionBombWarning:
                logging.warn('The file "{0}" contains a lot of pixels and '
                             'can take a lot of memory when decompressed. '
                             'To allow larger images, modify the '
                             '"max_decompressed_size" config.'
                             .format(self.fetch('filename')))
                # Use empty array as the file cannot be read.
                return numpy.ndarray(0)
        elif key == 'ndarray_grey':
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return skimage.img_as_ubyte(
                    skimage.color.rgb2grey(self.fetch('ndarray')))
        return super(ImageFile, self).fetch(key)

    def analyze_softwares(self):
        """
        Find the software used to create the given file with. It uses the exif
        data to find the softare that was used to create the file. It gives out
        a curated a list of softwares.

        :return: dict with the keys:

             - Composite:Softwares - Tuple with the names of the softwares
                detected that have been used with this file.
                The possible softwares that can be found are:
                    Inkscape, MATLAB, ImageMagick, Adobe ImageReady,
                    Adobe Photoshop Elements, Adobe Photoshop Express,
                    Adobe Photoshop, Picasa, GIMP, Microsoft ICE, GNU Plot,
                    Chemtool, VectorFieldPlot, and Stella.
        """
        exif = self.exiftool()
        softwares = []

        if (exif.get('SVG:Output_extension', '') ==
                'org.inkscape.output.svg.inkscape'):
            softwares.append('Inkscape')

        for sw_key in ('PNG:Software', 'EXIF:Software'):
            sw = exif.get(sw_key, '').lower()
            if sw.startswith('matlab'):
                softwares.append('MATLAB')
            elif sw.startswith('imagemagick'):
                softwares.append('ImageMagick')
            elif sw.startswith('adobe imageready'):
                softwares.append('Adobe ImageReady')
            elif sw.startswith('adobe photoshop'):
                if sw.startswith('adobe photoshop elements'):
                    softwares.append('Adobe Photoshop Elements')
                elif sw.startswith('adobe photoshop express'):
                    softwares.append('Adobe Photoshop Express')
                else:
                    softwares.append('Adobe Photoshop')
            elif sw.startswith('picasa'):
                softwares.append('Picasa')
            elif sw.startswith('gimp'):
                softwares.append('GIMP')
            elif sw.startswith('microsoft ice '):
                softwares.append('Microsoft ICE')

        desc = exif.get('SVG:Desc', '').lower()
        if ' gnuplot ' in desc:
            softwares.append('GNU Plot')
        elif ' chemtool ' in desc:
            softwares.append('Chemtool')
        elif ' vectorfieldplot ' in desc:
            softwares.append('VectorFieldPlot')

        comment = exif.get('PNG:Comment', '').lower()
        if ' stella4d ' in comment:
            softwares.append('Stella')

        if len(softwares) == 0:
            return {}

        return {'Composite:Softwares':
                tuple(softwares) if len(softwares) > 1 else softwares[0]}

    def analyze_color_average(self):
        """
        Find the average RGB color of the image and compare with the existing
        Pantone color system to identify the color name.

        :return: dict with the keys:

             - Color:ClosestLabeledColorRGB - The closest RGB value of the
                color found in the Pantone color palette.
             - Color:ClosestLabeledColorRGB - The name of the closest color
                found in the Pantone color palette.
             - Color:AverageRGB - The average RGB value of the image.
        """
        image_array = self.fetch('ndarray')
        if image_array.ndim == 4:  # Animated images
            mean_color = image_array.mean(axis=(0, 1, 2))
        elif image_array.ndim == 3:  # Static images
            mean_color = image_array.mean(axis=(0, 1))
        elif image_array.ndim == 2:  # Greyscale images
            avg = image_array.mean()
            mean_color = (avg, avg, avg)
        else:
            msg = ('Unsupported image type in "analyze_color_average()". '
                   'Expected animated, greyscale, rgb, or rgba images. '
                   'Found an image with {0} dimensions and shape {1}. '
                   .format(image_array.ndim, image_array.shape))
            logging.warn(msg)
            return {}

        mean_color = mean_color[:3]  # Remove alpha channel if existent
        closest_label, closest_color = PantonePaint().find_closest(mean_color)

        return {
            'Color:ClosestLabeledColorRGB': closest_color,
            'Color:ClosestLabeledColor': closest_label,
            'Color:AverageRGB': tuple(round(i, 3) for i in mean_color)}

    @staticmethod
    def _haarcascade(image, filename, directory=None, **kwargs):
        """
        Use OpenCV's haarcascade classifiers to detect certain features.

        :param image:     Image to use when detecting with the haarcascade.
        :param filename:  The file to create the CascadeClassifier with.
        :param directory: The directory of the haarcascade file.
        :param kwagrs:    Keyword args to pass to cascade's detectMultiScale().
        :return:          List of rectangles of the detected objects. A rect
                          is defined by an array with 4 values i the order:
                          left, top, width, height.
        """
        try:
            import cv2
        except ImportError:
            logging.warn('HAAR Cascade analysis requires the optional '
                         'dependency OpenCV to be installed.')
            return []

        directory = (directory if directory is not None
            else os.path.abspath(os.path.join(
                os.path.realpath(cv2.__file__),
                *([os.pardir] * 4 + ['share', 'OpenCV', 'haarcascades']))))
        cascade = cv2.CascadeClassifier(os.path.join(directory, filename),)
        features = cascade.detectMultiScale(image, **kwargs)
        return features

    def analyze_face_haarcascades(self):
        """
        Use opencv's haar cascade filters to identify faces, right eye, left
        eye, upper body, etc..
        """
        try:
            import cv2
            from cv2 import cv
        except ImportError:
            logging.warn('HAAR Cascade analysis requires the optional '
                         'dependency OpenCV 2.x to be installed.')
            return {}

        image_array = self.fetch('ndarray_grey')
        if image_array.ndim == 3:
            logging.warn('Faces cannot be detected in animated images '
                         'using haarcascades yet.')
            return {}

        # The "scale" given here is relevant for the detection rate.
        scale = max(1.0, numpy.average(image_array.shape) / 500.0)

        # Equalize the histogram and make the size smaller
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            img_shape = map(lambda x: int(x / scale), image_array.shape)
            img = skimage.img_as_ubyte(
                skimage.exposure.equalize_hist(
                    skimage.transform.resize(image_array,
                                             output_shape=img_shape,
                                             preserve_range=True)))

        def haar(im, key, single=False, **kwargs):
            cascades = {
                'frontal_face': 'haarcascade_frontalface_alt.xml',
                'profile_face': 'haarcascade_profileface.xml',
                'nested': 'haarcascade_eye_tree_eyeglasses.xml',
                'mouth': 'haarcascade_mcs_mouth.xml',
                'nose': 'haarcascade_mcs_nose.xml',
                'right_eye': 'haarcascade_righteye_2splits.xml',
                'left_eye': 'haarcascade_lefteye_2splits.xml',
                'left_ear': 'haarcascade_mcs_leftear.xml',
                'right_ear': 'haarcascade_mcs_rightear.xml',
                'upper_body': 'haarcascade_upperbody.xml',
                'lower_body': 'haarcascade_lowerbody.xml'}
            # Set some default kwargs
            kwargs['scaleFactor'] = kwargs.get('scaleFactor', 1.1)
            kwargs['minNeighbors'] = kwargs.get('minNeighbors', 2)
            kwargs['minSize'] = kwargs.get('minSize', (30, 30))
            flags = cv.CV_HAAR_SCALE_IMAGE
            if single:
                flags = (flags | cv.CV_HAAR_FIND_BIGGEST_OBJECT |
                         cv.CV_HAAR_DO_ROUGH_SEARCH)
            kwargs['flags'] = kwargs.get('flags', flags)
            return list(self._haarcascade(im, cascades[key], **kwargs))

        def drop_overlapping_regions(regions):
            drop = set()
            # Sort regions by area (leftmost is smallest and dropped first)
            regions = sorted(regions, key=lambda x: x[-1] * x[-2])
            # overlap: Neither range is completely greater than the other
            overlap = (lambda x_min, x_width, y_min, y_width:
                       x_min <= y_min + y_width and y_min <= x_min + x_width)
            for i1, reg1 in enumerate(regions):
                for i2, reg2 in enumerate(regions[:i1]):
                    if (i2 not in drop and
                            overlap(reg1[0], reg1[2], reg2[0], reg2[2]) and
                            overlap(reg1[1], reg1[3], reg2[1], reg2[3])):
                        drop.add(i2)
            for i, reg in enumerate(regions):
                if i not in drop:
                    yield reg

        frontal = haar(img, 'frontal_face')
        profile = haar(img, 'profile_face')
        faces = list(drop_overlapping_regions(frontal + profile))

        if len(faces) == 0:
            return {}

        data = []
        for face in faces:
            scaled_face = list(map(lambda x: int(x * scale), face))
            fdata = {'position': {
                'left': scaled_face[0], 'top': scaled_face[1],
                'width': scaled_face[2], 'height': scaled_face[3]}}
            roi = list(map(int, [
                max(0, face[0] - (face[2] / 8)),
                max(0, face[1] - (face[3] / 8)),
                min(img.shape[0], face[2] + (2 * face[2] / 8)),
                min(img.shape[1], face[3] + (2 * face[3] / 8))]))
            face_img = img[roi[1]:roi[1] + roi[3] - 1,
                           roi[0]:roi[0] + roi[2] - 1]

            def feat_mid(rect, offx, offy):
                return (int(scale * (roi[0] + rect[0] + offx + rect[2] / 2)),
                        int(scale * (roi[1] + rect[1] + offy + rect[3] // 2)))

            eye_img = face_img[:roi[3] // 2, :]
            nested = list(drop_overlapping_regions(haar(eye_img, 'nested')))
            if len(nested) == 2:
                nested = sorted(nested, key=lambda x: x[0])
                fdata['eyes'] = (feat_mid(nested[0], 0, 0),
                                 feat_mid(nested[1], 0, 0))
            else:
                eyes_found = []
                for eye in ['left_eye', 'right_eye']:
                    eye_feats = haar(eye_img, eye, single=True)
                    if len(eye_feats) == 1:
                        eyes_found.append(feat_mid(eye_feats[0], 0, 0))
                if len(eyes_found) > 0:
                    fdata['eyes'] = tuple(eyes_found)

            ear_offy = roi[3] // 8
            ear_img = face_img[ear_offy:roi[3] * 7 // 8, :]
            ears_found = []
            for ear in ['left_ear', 'right_ear']:
                ear_feats = haar(ear_img, ear, single=True)
                if len(ear_feats) == 1:
                    ears_found.append(feat_mid(ear_feats[0], 0, ear_offy))
            if len(ears_found) > 0:
                fdata['ears'] = tuple(ears_found)

            nose_offx, nose_offy = roi[2] // 4, roi[3] // 4
            nose_img = face_img[nose_offy:roi[3] * 3 // 4,
                                nose_offx:roi[2] * 3 // 4]
            nose_feats = haar(nose_img, 'nose', single=True)
            if len(nose_feats) == 1:
                fdata['nose'] = feat_mid(nose_feats[0], nose_offx, nose_offy)

            mouth_offy = roi[3] // 2
            mouth_img = face_img[mouth_offy:, :]
            mouth_feats = haar(mouth_img, 'mouth', single=True)
            if len(mouth_feats) == 1:
                fdata['mouth'] = feat_mid(mouth_feats[0], 0, mouth_offy)

            data.append(fdata)
        return {'OpenCV:Faces': data}

    def analyze_facial_landmarks(self,
                                 with_landmarks=True,
                                 detector_upsample_num_times=0):
        """
        Use ``dlib`` to find the facial landmarks and also detect pose.

        Note: It works only for frontal faces, not for profile faces, etc.

        :param with_landmarks:
            Whether to detect the facial landmarks or not. This also computes
            the location of the other facial features like the nose, mouth,
            and eyes.
        :param detector_upsample_num_times:
            The number of times to upscale the image by when detecting faces.
        :return: dict with the keys:

             - dlib:Faces - A dictionary with information about the face:
                - position - Dict with corner information having the keys
                    left, right, top, bottom.
                - score - A score given on the probability of the given
                    feture being a face.
                If the kwarg `with_landmarks` is provided, it also gives the
                following information:
                - nose - Location of the center of the nose.
                - left eye - Location of the center of the left eye.
                - right eye - Location of the center of the right eye.
                - mouth - Location of the center of the mouth.
        """
        image_array = self.fetch('ndarray')
        if len(image_array.shape) == 4:
            logging.warn('Facial landmarks of animated images cannot be '
                         'detected yet.')
            return {}

        if len(image_array.shape) == 3 and image_array.shape[2] == 4:
            # RGBA is not supported, Hence convert it to RGB
            image_array = image_array[:, :, :3].copy()
            # The .copy() is needed because of the dlib `shape` finding issue:
            # https://github.com/davisking/dlib/issues/128

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
                             'width': face.right() - face.left() + 1,
                             'height': face.bottom() - face.top() + 1},
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
                # Point 46 and 43 are the two corners of the right eye
                fdata['eyes'] = (tup2(shape.part(40), shape.part(37)),
                                 tup2(shape.part(46), shape.part(43)))
                # Point 49 and 55 are the two outer corners of the mouth
                fdata['mouth'] = tup2(shape.part(49), shape.part(55))
            data.append(fdata)

        return {'dlib:Faces': data}

    def analyze_barcode_zxing(self):
        """
        Use ``zxing`` to find barcodes, qr codes, data matrices, etc.
        from the image.

        :return: dict with the keys:

             - zxing:Barcodes - An array containing information about barcodes.
                Each barcode is encoded to a dictionary with the keys:
                - format - The format of the barcode. Example: QR_CODE,
                    CODABAR, DATA_MATRIX, etc.
                - data - The text data that is encdoded in the barcode.
                - bounding box - A dictionary with left, width, top, height.
                - points - The detection points of the barcode (4 points for
                    QR codes and Data matrices and 2 points for barcodes).
        """
        if all(map(lambda x: x < 4, self.fetch('ndarray').shape)):
            # If the file is less than 4 pixels, it won't contain a barcode.
            # Small files cause zxing to crash so, we just return empty.
            return {}

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

            bbox = {}
            if num_pts == 2:  # left, right
                l, r = [(int(i), int(j)) for (i, j) in points]
                bbox = {"left": l[0], "top": l[1],
                        "width": r[0] - l[0] + 1, "height": r[1] - l[1] + 1}
            elif num_pts == 4:  # bottomLeft, topLeft, topRight, bottomRight
                lb, lt, rt, rb = [(int(i), int(j)) for (i, j) in points]
                bbox = {"left": min(lb[0], lt[0]),
                        "top": min(lt[1], rt[1]),
                        "width": max(rb[0] - lb[0], rt[0] - lt[0]),
                        "height": max(rb[1] - rt[1], lb[1] - lt[1])}

            barcodes.append({'format': _format, 'points': points,
                             'raw_data': raw_result, 'data': parsed_result,
                             'bounding box': bbox})

        return {'zxing:Barcodes': barcodes}

    def analyze_barcode_zbar(self):
        """
        Use ``zbar`` to find barcodes and qr codes from the image.

        :return: dict with the keys:

             - zbar:Barcodes - An array containing information about barcodes.
                Each barcode is encoded to a dictionary with the keys:
                - format - The format of the barcode. Example: QRCODE,
                    I25, etc.
                - data - The text data that is encdoded in the barcode.
                - bounding box - A dictionary with left, width, top, height.
                - confidence - The quality of the barcode. The higher it is
                    the more accurate the detection is.
        """
        image_array = self.fetch('ndarray_grey')
        if image_array.ndim == 3:
            logging.warn('Barcodes cannot be detected in animated images '
                         'using zbar.')
            return {}
        height, width = image_array.shape
        zbar_img = zbar.Image(width, height, 'Y800', image_array.tobytes())
        scanner = zbar.ImageScanner()
        scanner.parse_config('enable')
        if scanner.scan(zbar_img) == 0:
            return {}

        barcodes = []
        for barcode in zbar_img:
            p = numpy.array(barcode.location)
            bbox = {"left": min(p[:, 0]), "top": min(p[:, 1]),
                    "width": max(p[:, 0]) - min(p[:, 0]),
                    "height": max(p[:, 1]) - min(p[:, 1])}
            barcodes.append({'data': barcode.data,
                             'bounding box': bbox,
                             'confidence': barcode.quality,
                             'format': str(barcode.type)})
        return {'zbar:Barcodes': barcodes}

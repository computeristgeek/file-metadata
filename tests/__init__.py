# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

# flake8: noqa (unused import and line too long due to links)

import os
import random
import string
import struct
import wave

try:
    import unittest
except ImportError:
    import unittest2 as unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock

from file_metadata._compat import makedirs, which
from file_metadata.utilities import download

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

file_download_links = {
    # Audio
    'wikiexample.ogg': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg',
    'drums.mid': 'https://upload.wikimedia.org/wikipedia/commons/6/61/Drum_sample.mid',
    'bell.wav': 'https://upload.wikimedia.org/wikipedia/commons/9/97/156064_marcolo91_bicycle-bell.wav',
    'bell.flac': 'https://upload.wikimedia.org/wikipedia/commons/b/b2/Bell-ring.flac',
    'bell.oga': 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Announcement_on_a_wharf.oga',
    'bell.ogg': 'https://upload.wikimedia.org/wikipedia/commons/3/34/Sound_Effect_-_Door_Bell.ogg',

    # Videos
    'veins.ogv': 'https://upload.wikimedia.org/wikipedia/commons/f/f2/POROS_3.ogv',
    'ogg_video.ogg': 'https://upload.wikimedia.org/wikipedia/commons/e/e3/2010-06-06-V-German-Flag.ogg',

    # Images
    'ball.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/1-ball.svg/226px-1-ball.svg.png',
    'ball.svg': 'https://upload.wikimedia.org/wikipedia/commons/5/51/1-ball.svg',
    'red.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Pure_Red.svg/100px-Pure_Red.svg.png',
    'green.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Pure_Green.svg/100px-Pure_Green.svg.png',
    'blue.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Pure_Blue.svg/100px-Pure_Blue.svg.png',
    'red.svg': 'https://upload.wikimedia.org/wikipedia/commons/6/62/Pure_Red.svg',
    'green.svg': 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Pure_Green.svg',
    'blue.svg': 'https://upload.wikimedia.org/wikipedia/commons/7/77/Pure_Blue.svg',
    'animated.svg': 'https://upload.wikimedia.org/wikipedia/commons/f/fd/Animated_pendulum.svg',
    'animated.gif': 'https://upload.wikimedia.org/wikipedia/commons/d/d7/123_Numbers.gif',
    'animated.png': 'https://upload.wikimedia.org/wikipedia/commons/b/b5/Load.png',
    'static.gif': 'https://upload.wikimedia.org/wikipedia/commons/e/ed/Pix.gif',
    'cmyk.jpg': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/17-barcodes-1-e_ces_2012_01.jpg/524px-17-barcodes-1-e_ces_2012_01.jpg',
    'unknown_cmyk.jpg': 'https://upload.wikimedia.org/wikipedia/commons/f/f3/TeXML_dtd.jpg',

    # SVG files with different mimetypes
    'image_svg_xml.svg': 'https://upload.wikimedia.org/wikipedia/commons/6/62/Pure_Red.svg',
    'text_plain.svg': 'https://upload.wikimedia.org/wikipedia/commons/5/57/Color_icon_white.svg',
    'text_html.svg': 'https://upload.wikimedia.org/wikipedia/commons/f/fd/Animated_pendulum.svg',
    'application_xml.svg': 'https://upload.wikimedia.org/wikipedia/commons/0/0b/Sieve_of_Eratosthenes_animation.svg',

    # Images with special exifdata:
    'canon_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Annagrah-2_041.JPG',

    # Images of faces
    'mona_lisa.jpg': 'https://upload.wikimedia.org/wikipedia/commons/7/7d/Mona_Lisa_color_restoration.jpg',
    'michael_jackson.jpg': 'https://upload.wikimedia.org/wikipedia/commons/7/7e/Michaeljackson_%28cropped%29.jpg',
    'charlie_chaplin.jpg': 'https://upload.wikimedia.org/wikipedia/commons/0/00/Charlie_Chaplin.jpg',
    'baby_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Portrait_of_a_male_baby_%285866018681%29.jpg',
    'baby_partial_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/1f/Sweet_Baby_Kisses_Family_Love.jpg',
    'old_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/11/Brazil_%283042571516%29_%282%29.jpg',
    'beard_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/6/61/Oskar_Almgren%2C_Stockholm%2C_Sweden_%285859501260%29_%282%29.jpg',
    'cat_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Savannah_Cat_portrait.jpg/400px-Savannah_Cat_portrait.jpg',
    'monkey_face.jpg': 'https://upload.wikimedia.org/wikipedia/commons/2/27/Baby_ginger_monkey.jpg',
    'woman.xcf': 'https://upload.wikimedia.org/wikipedia/commons/a/af/Beatrix_Podolska_pedagog_muzykolog_Krakow_2008.xcf',

    # Barcodes / QR Codes / Data matrices
    'qrcode.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/5b/Qrcode_wikipedia.jpg',
    'barcode.png': 'https://upload.wikimedia.org/wikipedia/commons/1/1f/Rationalized-codabar.png',
    'datamatrix.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Datamatrix.svg/200px-Datamatrix.svg.png',
    'multibarcodes.png': 'https://upload.wikimedia.org/wikipedia/commons/9/98/DHL_Online-Frankierung_-_Paket_bis_5_kg_-_D-USA.png',
    'vertical_barcode.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/9c/Final_Ida_Pasto_vs._Santa_Fe.jpg',

    'huge.png': 'https://upload.wikimedia.org/wikipedia/commons/3/31/Grand_paris_express.png',

    'blank.xcf': 'https://upload.wikimedia.org/wikipedia/commons/e/e2/Blank_file.xcf',
    'example.tiff': 'https://upload.wikimedia.org/wikipedia/commons/b/b0/Dabigatran_binding_pockets.tiff',
    'text.pdf': 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Life_of_Future.pdf',
    'image.pdf': 'https://upload.wikimedia.org/wikipedia/commons/4/40/AugerTransition1.pdf',

    # Files created by some software
    'bitmap_from_inkscape.png': 'https://upload.wikimedia.org/wikipedia/commons/4/41/Joetsu_Shinkansen_icon.png',
    'created_with_inkscape.svg': 'https://upload.wikimedia.org/wikipedia/commons/9/9a/Db-omega.svg',
    'created_with_matlab.png': 'https://upload.wikimedia.org/wikipedia/commons/d/d1/Fat_absoprtion.png',
    'created_with_imagemagick.png': 'https://upload.wikimedia.org/wikipedia/commons/9/99/Groz-01.PNG',
    'created_with_adobe_imageready.png': 'https://upload.wikimedia.org/wikipedia/commons/2/29/Holtz.png',
    'created_with_adobe_photoshop.jpg': 'https://upload.wikimedia.org/wikipedia/commons/6/64/Cervicomanubriotomie.jpg',
    'created_with_adobe_photoshop_express.jpg': 'https://upload.wikimedia.org/wikipedia/commons/b/b5/Politecnico_di_Milano_Bovisa_4.jpg',
    'created_with_adobe_photoshop_elements.jpg': 'https://upload.wikimedia.org/wikipedia/commons/4/49/1010_Bazylika_archikatedralna_%C5%9Bw_Jakuba_Szczecin_sygnaturka_0.jpg',
    'created_with_photoshop_photomerge.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/90/01-118_Koenigstein_Panorama.jpg',
    'created_with_picasa.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/1f/08_Ny_Alesund_prn.JPG',
    'created_with_gimp.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/d5/2013-04-25_21-09-18-ecl-lune-mosaic.jpg',
    'created_with_gimp_comment.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/c9/105_H_61-37.jpeg',
    'created_with_gnu_octave.svg': 'https://upload.wikimedia.org/wikipedia/commons/5/52/Beta_versus_rapidity.svg',
    'created_with_gnuplot.svg': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/2005_H-1B_admissions_by_country_of_citizenship.svg',
    'created_with_chemtool.svg': 'https://upload.wikimedia.org/wikipedia/commons/0/00/Chitobiose_glucosamine.svg',
    'created_with_vectorfieldplot.svg': 'https://upload.wikimedia.org/wikipedia/commons/8/83/VFPt_minus.svg',
    'created_with_stella.png': 'https://upload.wikimedia.org/wikipedia/commons/e/e8/10-3_deltohedron.png',
    'created_with_microsoft_image_composite_editor.jpg': 'https://upload.wikimedia.org/wikipedia/commons/7/7c/Bochnia_kopalnia_kaplica_2.jpg',
    'created_with_paint_net.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Broadway_Tower_Oil_Painting.jpg',
    'screenshot_with_gnome_screenshot.png': 'https://upload.wikimedia.org/wikipedia/commons/7/74/LibreOfficePresentationTeluguExample1.png',

    # Line drawings
    'simple_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/c6/Destilacija_rakije.jpg',
    'detailed_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/db/Compound_Microscope_1876.JPG',
    'very_detailed_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Hospital_ward_on_Red_Rover.jpg',
    'dark_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Bird_in_flight_line_drawing_art.jpg',

    # Logos
    'wikimedia_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Wikimedia-logo.svg/768px-Wikimedia-logo.svg.png',
    'wikidata_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Wikidata-logo.svg/1024px-Wikidata-logo.svg.png',
    'wikipedia_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Wikipedia_Logo_1.0.png/768px-Wikipedia_Logo_1.0.png',
    'commons_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Commons-logo.svg/571px-Commons-logo.svg.png'
}


def fetch_file(name, overwrite=False):
    """
    Fetch a file based on the given key. If the file is not found, it is
    created appropriately by either generating it or downloading it from
    elsewhere.

    :param name:      The name (key) of the file that is needed.
    :param overwrite: Force overwrite if file exists.
    :return:          The absolute path of the requested file.
    """
    filepath = os.path.join(CACHE_DIR, name)

    makedirs(CACHE_DIR, exist_ok=True)

    if os.path.exists(filepath) and not overwrite:  # Use cached file
        return filepath

    # Miscellaneous files
    if name == 'ascii.txt':
        with open(filepath, 'w') as file_handler:
            file_handler.writelines([
                string.ascii_lowercase, '\n', string.ascii_uppercase, '\n',
                string.digits, '\n', string.punctuation, '\n'])
    elif name == 'file.bin':
        with open(filepath, 'wb') as file_hander:
            allascii = ''.join(chr(i) for i in range(128))
            file_hander.write(allascii.encode('ascii'))
    # Music files
    elif name == "noise.wav":
        wav_file = wave.open(filepath, 'w')
        wav_file.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
        for _ in range(44100):  # 1 second
            value = struct.pack('h', random.randint(-32767, 32767))
            wav_file.writeframes(value)
        wav_file.close()
    elif name in file_download_links:
        download(file_download_links[name], filepath)
    else:
        raise ValueError('Asked to fetch unknown file {0}.'.format(name))

    return filepath


def which_sideeffect(unavailable_executables):
    def wrapper(command, *args, **kwargs):
        if command in unavailable_executables:
            return None
        return which(command, *args, **kwargs)
    return wrapper


def is_toolserver():
    return os.environ.get('INSTANCEPROJECT', None) == 'tools'


def is_travis():
    return os.environ.get('TRAVIS', None) == 'true'

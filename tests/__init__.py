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
    'multiline_ffprobe.ogg': 'https://upload.wikimedia.org/wikipedia/commons/5/58/17650_thoschi_issyk-kul.ogg',

    # Videos
    'veins.ogv': 'https://upload.wikimedia.org/wikipedia/commons/f/f2/POROS_3.ogv',
    'ogg_video.ogg': 'https://upload.wikimedia.org/wikipedia/commons/e/e3/2010-06-06-V-German-Flag.ogg',
    'sample.webm': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/02_Punktion_des_ausgebildeten_Knopflochs%281%29.webm',

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
    'nonascii_exifdata.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/d5/2013-04-25_21-09-18-ecl-lune-mosaic.jpg',

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

    # Line drawings
    'simple_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/c6/Destilacija_rakije.jpg',
    'detailed_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/db/Compound_Microscope_1876.JPG',
    'very_detailed_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Hospital_ward_on_Red_Rover.jpg',
    'dark_line_drawing.jpg': 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Bird_in_flight_line_drawing_art.jpg',

    # Logos
    'wikimedia_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Wikimedia-logo.svg/768px-Wikimedia-logo.svg.png',
    'wikidata_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Wikidata-logo.svg/1024px-Wikidata-logo.svg.png',
    'wikipedia_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Wikipedia_Logo_1.0.png/768px-Wikipedia_Logo_1.0.png',
    'commons_logo.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Commons-logo.svg/571px-Commons-logo.svg.png',

    # Geocoded images
    'geotag_osaka.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/50/Honda_STEPWGN_SPADA%E3%83%BBCool_Spirit_%28RP3%29_rear.JPG',

    # Monochrome colors
    'blackwhite_monochrome.jpg': 'https://upload.wikimedia.org/wikipedia/commons/2/27/0218_-_Taormina_-_Badia_Vecchia_-_Foto_Giovanni_Dall%27Orto%2C_20-May-2008.jpg',
    'blue_monochrome.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/9f/Paolo_Monti_-_Serie_fotografica_-_BEIC_6358396.jpg',
    'green_monochrome.jpg': 'https://upload.wikimedia.org/wikipedia/commons/e/ea/Edvard-dawkins.jpg',
    'sepia_monochrome.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/c7/1926_Hupmobile.jpg',

    # Color calibrations
    'it8_top_bar.jpg': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Waterfall_at_Schooner_Head_house_%28NYPL_b11707223-G89F198_003B%29.tiff/lossy-page1-1280px-Waterfall_at_Schooner_Head_house_%28NYPL_b11707223-G89F198_003B%29.tiff.jpg',
    'it8_bottom_bar.jpg': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Two_boys_sitting_in_a_garden_%28NYPL_b11528957-G90F452_008B%29.tiff/lossy-page1-996px-Two_boys_sitting_in_a_garden_%28NYPL_b11528957-G90F452_008B%29.tiff.jpg',

    # Application files
    'text.pdf': 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Life_of_Future.pdf',
    'image.pdf': 'https://upload.wikimedia.org/wikipedia/commons/4/40/AugerTransition1.pdf',
    'empty.djvu': 'https://upload.wikimedia.org/wikipedia/commons/4/42/Vuota.djvu',
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

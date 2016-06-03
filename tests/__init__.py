# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import random
import string
import struct
import wave

try:  # Python 2
    import unittest2 as unittest
except ImportError:
    import unittest

try:  # Python 3
    import unittest.mock as mock  # flake8: noqa (unused import)
except ImportError:  # Python 2
    import mock  # flake8: noqa (unused import)

from file_metadata.utilities import download

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

file_download_links = {
    'wikiexample.ogg': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg',
    'veins.ogv': 'https://upload.wikimedia.org/wikipedia/commons/f/f2/POROS_3.ogv',
    'drums.mid': 'https://upload.wikimedia.org/wikipedia/commons/6/61/Drum_sample.mid',
    'ball.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/1-ball.svg/226px-1-ball.svg.png',
    'ball.svg': 'https://upload.wikimedia.org/wikipedia/commons/5/51/1-ball.svg',
    'red.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Pure_Red.svg/100px-Pure_Red.svg.png',
    'green.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Pure_Green.svg/100px-Pure_Green.svg.png',
    'blue.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Pure_Blue.svg/100px-Pure_Blue.svg.png',
    'red.svg': 'https://upload.wikimedia.org/wikipedia/commons/6/62/Pure_Red.svg',
    'green.svg': 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Pure_Green.svg',
    'blue.svg': 'https://upload.wikimedia.org/wikipedia/commons/7/77/Pure_Blue.svg',

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

    # Barcodes / QR Codes / Data matrices
    'qrcode.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/5b/Qrcode_wikipedia.jpg',
    'barcode.png': 'https://upload.wikimedia.org/wikipedia/commons/1/1f/Rationalized-codabar.png',
    'datamatrix.png': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Datamatrix.svg/200px-Datamatrix.svg.png',
    'multibarcodes.png': 'https://upload.wikimedia.org/wikipedia/commons/9/98/DHL_Online-Frankierung_-_Paket_bis_5_kg_-_D-USA.png'}


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

    if not os.path.isdir(CACHE_DIR):  # Make folder is it doesn't exist
        os.makedirs(CACHE_DIR)

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
        raise ValueError('Asked to fetch unknown file.')

    return filepath


def importable(modulename):
    """
    Check if the given module can be imported or not.
    """
    try:
        _ = __import__(modulename)
        return True
    except ImportError:
        return False


def is_toolserver(self):
    return os.environ.get('INSTANCEPROJECT', None) == 'tools'


def is_travis(self):
    return os.environ.get('TRAVIS', None) == 'true'

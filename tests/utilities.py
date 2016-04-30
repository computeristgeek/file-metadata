import os
import string

try:  # Python 3
    import unittest.mock as mock  # flake8: noqa (unused import)
except ImportError:  # Python 2
    import mock  # flake8: noqa (unused import)


CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'files')


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
    else:
        raise ValueError('Asked to fetch unknown file.')

    return filepath

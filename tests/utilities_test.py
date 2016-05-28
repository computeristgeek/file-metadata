# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import bz2
import imghdr
import os
import shutil
import socket
import tempfile
from io import StringIO

from file_metadata.utilities import (app_dir, bz2_decompress, make_temp,
                                     download, PropertyCached, DictNoNone)
from tests import mock, unittest


def active_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


class DownloadTest(unittest.TestCase):

    @mock.patch('file_metadata.utilities.urlopen')
    def test_text_data(self, mock_urlopen):
        mock_urlopen.return_value = StringIO()
        with make_temp() as filename:
            os.remove(filename)
            download('https://httpbin.org/ip', filename)
            self.assertTrue(mock_urlopen.called)

    @mock.patch('file_metadata.utilities.urlopen')
    def test_overwrite(self, mock_urlopen):
        mock_urlopen.return_value = StringIO()
        with make_temp() as filename:
            download('https://httpbin.org/ip', filename)
            mock_urlopen.assert_not_called()
            os.remove(filename)
            download('https://httpbin.org/ip', filename, overwrite=True)
            self.assertTrue(mock_urlopen.called)

    @unittest.skipIf(not active_internet(), 'Internet connection not found.')
    def test_binary_data(self):
        # Use this test to ensure that the data is appropriately caught from
        # the internet.
        with make_temp() as filename:
            os.remove(filename)
            download('https://httpbin.org/image/png', filename)
            self.assertEqual(imghdr.what(filename), "png")


class BZ2DecompressTest(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp(prefix='abdeali_')
        self.bzfile = os.path.join(self.testdir, 'bz2file')

    def tearDown(self):
        shutil.rmtree(self.testdir)

    def test_bz2(self):
        with open(self.bzfile + '.txt', 'w') as _file:
            _file.write('hello world')
        with open(self.bzfile + '.txt', 'rb') as textfile:
            _file = bz2.BZ2File(self.bzfile + '.bz2', 'wb')
            _file.write(textfile.read())
            _file.close()
        os.remove(self.bzfile + '.txt')

        bz2_decompress(self.bzfile + '.bz2', self.bzfile + '.txt')

        with open(self.bzfile + '.txt') as _file:
            self.assertEqual(_file.read().decode('utf-8'), 'hello world')


class PropertyCachedTest(unittest.TestCase):

    def test_non_class_property(self):
        @PropertyCached
        def prop():
            return 1

        self.assertNotEqual(prop, 1)
        self.assertTrue(type(prop), PropertyCached)


class DictNoNoneTest(unittest.TestCase):

    def test_constructor(self):
        self.assertEqual(DictNoNone({'a': 1, 'b': None, 'c': 3}),
                         {'a': 1, 'c': 3})

    def test_addition(self):
        data = DictNoNone()
        data['a'] = 1
        data['b'] = None
        self.assertEqual(data, {'a': 1})


class AppDirTest(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.testdir)

    def test_invalid_dirtype(self):
        self.assertEqual(app_dir('unknown_function'), None)

    @mock.patch('file_metadata.utilities.appdirs')
    def test_check_paths(self, mock_appdirs):
        confdir = os.path.join(self.testdir, 'appdirs', 'configdir')
        mock_appdirs.user_config_dir = mock.Mock(return_value=confdir)

        self.assertFalse(os.path.exists(confdir))
        self.assertEqual(app_dir('user_config_dir'), confdir)
        self.assertTrue(os.path.exists(confdir))

        self.assertEqual(app_dir('user_config_dir', 'a', 'path'),
                         os.path.join(confdir, 'a', 'path'))

    def test_integration(self):
        self.assertTrue(os.path.exists(app_dir('user_data_dir')))

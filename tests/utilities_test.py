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

from six.moves.urllib.error import URLError

from file_metadata.utilities import (app_dir, bz2_decompress, make_temp,
                                     download, md5sum, memoized, DictNoNone)
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

    def test_timeout(self):
        with make_temp() as filename:
            os.remove(filename)
            self.assertRaises(URLError, download,
                              'https://httpbin.org/delay/3', filename,
                              timeout=1e-50)


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


class MD5SumTest(unittest.TestCase):

    def test_md5sum_small_file(self):
        with make_temp() as filename:
            with open(filename, 'w') as _file:
                _file.write('hello world!')
            self.assertEqual(md5sum(filename),
                             'fc3ff98e8c6a0d3087d515c0473f8677')

    def test_md5sum_large_file(self):
        with make_temp() as filename:
            with open(filename, 'w') as _file:
                _file.write('hello world!')
            self.assertEqual(md5sum(filename, blocksize=1),
                             'fc3ff98e8c6a0d3087d515c0473f8677')


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


class MemoizedTest(unittest.TestCase):

    def setUp(self):
        self.calls = 0
        self.arg0 = lambda: self.incr_calls()
        self.arg1 = lambda x: self.incr_calls() or x
        self.arg2 = lambda x, y = 0: self.incr_calls() or (x, y)
        # self.argv = lambda x, y, z = 0: self.incr_calls() or (x, y, z)
        self.kwargv = lambda *a: self.incr_calls() or a
        self.argv_kwargv = lambda x, y = 0, *a, **k: (
            self.incr_calls() or (x, y, a, k))

    def incr_calls(self):
        self.calls += 1

    def multicall(self, func, args_expr, expected_calls, num_calls=10):
        self.calls = 0
        results = [eval("f(%s)" % args_expr, {}, {"f": func})
                   for _ in xrange(num_calls)]
        self.assertEqual(self.calls, expected_calls)
        self.assertTrue(all(r == results[0] for r in results))
        return results[0]

    def assert_memoized(self, func, args_expr, deco=None):
        deco = deco or memoized
        self.assertEqual(self.multicall(func, args_expr, 10, 10),
                         self.multicall(deco(func), args_expr, 1, 10))

    def test_zero_arg(self):
        for func in self.arg0, self.kwargv:
            self.assert_memoized(func, "")

    def test_one_arg_pos(self):
        for f in self.arg1, self.arg2, self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "1")

    def test_one_arg_name(self):
        for f in self.arg2, self.argv_kwargv:
            self.assert_memoized(f, "x=1")

    def test_two_args_pos(self):
        for f in self.arg2, self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "1, 2")

    def test_two_args_named(self):
        for f in self.arg2, self.argv_kwargv:
            self.assert_memoized(f, "1, y=2")
            self.assert_memoized(f, "x=1, y=2")

    def test_varargs(self):
        for f in self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "*range(10)")

    def test_varargs_kwargs(self):
        self.assert_memoized(self.argv_kwargv, "x=1, z=5")
        self.assert_memoized(self.argv_kwargv, "1, 2, 3, 4, z=5")

    def test_unhashable(self):
        deco = memoized(hashable=False)
        for f in self.arg1, self.arg2, self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "[2]", deco)
            self.assert_memoized(f, "{'foo': 3}", deco)
        for f in self.arg2, self.argv_kwargv:
            self.assert_memoized(f, "x=[2]", deco)
            self.assert_memoized(f, "x={'foo': 3}", deco)
        for f in self.arg2, self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "[2], {'foo': 3}", deco)
        for f in self.arg2, self.argv_kwargv:
            self.assert_memoized(f, "[2], y={'foo': 3}", deco)
            self.assert_memoized(f, "x=[2], y={'bar': 2}", deco)

        for f in self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "[2], {'foo': 3}, 3", deco)

        for f in (self.argv_kwargv,):
            self.assert_memoized(f, "[2], {'foo': 3}, z={1,2}", deco)
            self.assert_memoized(f, "[2], y={'foo': 3}, z={1,2}", deco)
            self.assert_memoized(f, "x=[2], y={'foo': 3}, z={1,2}", deco)

        for f in self.kwargv, self.argv_kwargv:
            self.assert_memoized(f, "*[[] for _ in range(10)]", deco)

        self.assert_memoized(self.argv_kwargv, "x=[2], z={'foo': 3}", deco)
        self.assert_memoized(self.argv_kwargv,
                             "1, [2], {'foo': 3}, 4, z={5,6}", deco)

    def test_method(self):
        incr_calls = self.incr_calls

        class X(object):

            def arg0(self):
                incr_calls()

            bad_mf0 = memoized()(arg0)
            good_mf0 = memoized(is_method=True)(arg0)

        x = X()
        self.assertEqual(self.multicall(x.arg0, "", 10),
                         self.multicall(x.good_mf0, "", 1))

        with self.assertRaises(TypeError):
            x.bad_mf0()

    def test_default_decorator(self):
        @memoized
        def func():
            return self.arg0()
        self.multicall(func, "", 1)

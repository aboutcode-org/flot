#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import os
import os.path as osp
import zipfile
from contextlib import contextmanager

from testpath import assert_isdir
from testpath import assert_isfile
from testpath.tempdir import TemporaryDirectory

from flot import buildapi

data_dir = osp.join(osp.dirname(__file__), "data")


@contextmanager
def cwd(directory):
    prev = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(prev)


def test_build_wheel():
    with TemporaryDirectory() as td, cwd(osp.join(data_dir, "pep517")):
        filename = buildapi.build_wheel(td)
        assert str(filename).endswith(".whl"), filename
        assert_isfile(osp.join(td, filename))
        assert zipfile.is_zipfile(osp.join(td, filename))
        with zipfile.ZipFile(osp.join(td, filename)) as zipped:
            assert "module1.py" in zipped.namelist()
            assert "module1.pth" not in zipped.namelist()


def test_build_wheel_pep621():
    with TemporaryDirectory() as td, cwd(osp.join(data_dir, "pep621")):
        filename = buildapi.build_wheel(td)
        assert str(filename).endswith(".whl"), filename
        assert_isfile(osp.join(td, filename))
        assert zipfile.is_zipfile(osp.join(td, filename))


def test_prepare_metadata_for_build_wheel():
    with TemporaryDirectory() as td, cwd(osp.join(data_dir, "pep517")):
        dirname = buildapi.prepare_metadata_for_build_wheel(td)
        assert dirname.endswith(".dist-info"), dirname
        assert_isdir(osp.join(td, dirname))
        assert_isfile(osp.join(td, dirname, "METADATA"))

#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import os
import os.path as osp
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest
from testpath import assert_isdir
from testpath import assert_isfile

from flot import __version__
from flot import buildapi

"""Tests of flot building itself"""


@pytest.fixture()
def cwd_project():
    proj_dir = osp.dirname(osp.dirname(osp.abspath(buildapi.__file__)))
    if not osp.isfile(osp.join(proj_dir, "pyproject.toml")):
        pytest.skip("need flot source directory")

    old_cwd = os.getcwd()
    try:
        os.chdir(proj_dir)
        yield
    finally:
        os.chdir(old_cwd)


def test_prepare_metadata(tmp_path, cwd_project):
    tmp_path = str(tmp_path)
    dist_info = buildapi.prepare_metadata_for_build_wheel(tmp_path)

    assert dist_info.endswith(".dist-info")
    assert dist_info.startswith("flot")
    dist_info = osp.join(tmp_path, dist_info)
    assert_isdir(dist_info)

    assert_isfile(osp.join(dist_info, "WHEEL"))
    assert_isfile(osp.join(dist_info, "METADATA"))


def test_wheel(tmp_path, cwd_project):
    tmp_path = str(tmp_path)
    filename = buildapi.build_wheel(tmp_path)

    assert filename.endswith(".whl")
    assert filename.startswith("flot")
    path = osp.join(tmp_path, filename)
    assert_isfile(path)
    assert zipfile.is_zipfile(path)


def unpack(path):
    z = zipfile.ZipFile(str(path))
    t = tempfile.TemporaryDirectory()
    z.extractall(t.name)
    return t


def test_editable(tmp_path, cwd_project):
    tmp_path = str(tmp_path)
    filename = buildapi.build_editable(tmp_path)

    assert filename.endswith(".whl")
    assert filename.startswith("flot")
    path = osp.join(tmp_path, filename)
    assert_isfile(path)
    assert zipfile.is_zipfile(path)
    with unpack(path) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        pth_path = Path(unpacked, "flot.pth")
        assert pth_path.read_text().endswith("flot\n")

        dist_info = f"flot-{__version__}.dist-info"
        assert files == [
            f"{dist_info}/LICENSE",
            f"{dist_info}/METADATA",
            f"{dist_info}/RECORD",
            f"{dist_info}/WHEEL",
            f"{dist_info}/entry_points.txt",
            f"flot.pth",
        ]


def test_sdist(tmp_path, cwd_project):
    tmp_path = str(tmp_path)
    filename = buildapi.build_sdist(tmp_path)

    assert filename.endswith(".tar.gz")
    assert filename.startswith("flot")
    path = osp.join(tmp_path, filename)
    assert_isfile(path)
    assert tarfile.is_tarfile(path)

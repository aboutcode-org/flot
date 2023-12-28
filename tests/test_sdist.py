#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import shutil
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

from testpath import assert_isfile

from flot.sdist import SdistBuilder
from flot.sdist import clean_tarinfo
from flot.sdist import make_sdist

data_dir = Path(__file__).parent / "data"


def unpack(path):
    t = tempfile.TemporaryDirectory()
    shutil.unpack_archive(str(path), extract_dir=t.name)
    return t


def list_tar(path):
    with tarfile.open(path) as tf:
        return sorted(tf.getnames())


def test_make_sdist(tmp_path):
    # Smoke test of making a complete sdist
    builder = SdistBuilder.from_pyproject_file(data_dir / "package1" / "pyproject.toml")
    sd = builder.build(tmp_path)
    assert_isfile(tmp_path / "package1-0.0.1.tar.gz")

    with unpack(sd) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "package1-0.0.1/PKG-INFO",
            "package1-0.0.1/__init__.py",
            "package1-0.0.1/data_dir/foo.sh",
            "package1-0.0.1/foo.py",
            "package1-0.0.1/package1/__init__.py",
            "package1-0.0.1/package1/data_dir/foo.sh",
            "package1-0.0.1/package1/foo.py",
            "package1-0.0.1/package1/subpkg/__init__.py",
            "package1-0.0.1/package1/subpkg/sp_data_dir/test.json",
            "package1-0.0.1/package1/subpkg2/__init__.py",
            "package1-0.0.1/pyproject.toml",
            "package1-0.0.1/subpkg/__init__.py",
            "package1-0.0.1/subpkg/sp_data_dir/test.json",
            "package1-0.0.1/subpkg2/__init__.py",
        ]


def test_make_sdist_with_extra_includes_and_ignored_wheel_suffix_strips(tmp_path):
    # Smoke test of making a complete sdist
    builder = SdistBuilder.from_pyproject_file(data_dir / "module5" / "pyproject.toml")
    sd = builder.build(tmp_path)

    with unpack(sd) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "module3-1.0/LICENSE",
            "module3-1.0/PKG-INFO",
            "module3-1.0/pyproject.toml",
            "module3-1.0/src/module3.py",
            "module3-1.0/src/module4.py",
        ]


def test_make_sdist_with_extra_includes_and_ignored_wheel_suffix_strips_and_rename_pyproject(
    tmp_path,
):
    builder = SdistBuilder.from_pyproject_file(data_dir / "module6" / "not-py-project.foo")
    sd = builder.build(tmp_path)

    with unpack(sd) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "module3-1.0/LICENSE",
            "module3-1.0/PKG-INFO",
            "module3-1.0/extras/some.txt",
            "module3-1.0/pyproject.toml",
            "module3-1.0/src/deep/nested/foo.py",
            "module3-1.0/src/module3.py",
            "module3-1.0/src/module4.py",
        ]


def test_make_sdist_pep621(tmp_path):
    sd = make_sdist(pyproject_file=data_dir / "pep621" / "pyproject.toml", output_dir=tmp_path)
    assert sd.name == "module1-1.0.0.tar.gz"
    assert_isfile(sd)


def test_make_sdist_pep621_nodynamic(tmp_path):
    builder = SdistBuilder.from_pyproject_file(data_dir / "pep621_nodynamic" / "pyproject.toml")
    path = builder.build(tmp_path)
    assert path == tmp_path / "module1-0.3.tar.gz"
    assert_isfile(path)


def test_clean_tarinfo():
    with tarfile.open(mode="w", fileobj=BytesIO()) as tf:
        ti = tf.gettarinfo(str(data_dir / "module1.py"))
    cleaned = clean_tarinfo(ti, mtime=42)
    assert cleaned.uid == 0
    assert cleaned.uname == ""
    assert cleaned.mtime == 42


def test_include_exclude():
    builder = SdistBuilder.from_pyproject_file(data_dir / "inclusion" / "pyproject.toml")
    files = sorted(str(rel) for _abs, rel in builder._select_all_files())
    expected = [
        "LICENSES/README",
        "doc/subdir/test.txt",
        "doc/test.rst",
        "module1.py",
        "pyproject.toml",
    ]
    assert files == expected


def test_data_dir():
    builder = SdistBuilder.from_pyproject_file(data_dir / "with_data_dir" / "pyproject.toml")
    files = sorted(str(rel) for _abs, rel in builder._select_all_files())
    expected = ["LICENSE", "data/share/man/man1/foo.1", "pyproject.toml"]
    assert files == expected


def test_pep625(tmp_path):
    builder = SdistBuilder.from_pyproject_file(data_dir / "normalization" / "pyproject.toml")
    path = builder.build(tmp_path)
    assert path == tmp_path / "my_python_module-0.0.1.tar.gz"
    assert_isfile(path)


def test_SdistBuilder_build_with_scripts(
    tmp_path,
    copy_test_data,
):
    td = copy_test_data("scripts")
    builder = SdistBuilder.from_pyproject_file(td / "not-py-project.foo")
    sd = builder.build(tmp_path)

    with unpack(sd) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "module3-1.0/LICENSE",
            "module3-1.0/PKG-INFO",
            "module3-1.0/etc/scripts/sdist.py",
            "module3-1.0/etc/scripts/wheel.py",
            "module3-1.0/extras/some.txt",
            "module3-1.0/pyproject.toml",
            "module3-1.0/somenewfile-sdist.txt",
            "module3-1.0/src/deep/nested/foo.py",
            "module3-1.0/src/module3.py",
            "module3-1.0/src/module4.py",
        ]


def test_SdistBuilder_does_create_duplicate_tar_entries(
    tmp_path,
    copy_test_data,
):
    td = copy_test_data("no-dupe-includes-in-sdist")
    builder = SdistBuilder.from_pyproject_file(td / "pyproject.toml")
    sd = builder.build(tmp_path)

    files = list_tar(sd)
    assert files == [
        "packagedcode-32.0.8/LICENSE",
        "packagedcode-32.0.8/PKG-INFO",
        "packagedcode-32.0.8/module.py",
        "packagedcode-32.0.8/pyproject.toml",
    ]

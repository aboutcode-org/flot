#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import configparser
import os
import stat
import tempfile
import zipfile
from pathlib import Path
from unittest import skipIf
from zipfile import ZipFile

from testpath import assert_isdir
from testpath import assert_isfile

from flot.wheel import WheelBuilder
from flot.wheel import make_wheel

data_dir = Path(__file__).parent / "data"


def test_WheelBuilder_select_files():
    pyproject_file = data_dir / "inclusion" / "pyproject.toml"
    base_dir = pyproject_file.parent
    wb = WheelBuilder.from_pyproject_file(pyproject_file)
    files = [(str(a.relative_to(base_dir)), str(b)) for a, b in wb.selected_files.files]
    assert files == [("module1.py", "module1.py")]


def test_inclusion_dir(tmp_path):
    # Smoketest for https://github.com/pypa/flit/issues/399
    wheel = make_wheel(
        pyproject_file=data_dir / "inclusion" / "pyproject.toml", output_dir=tmp_path
    )
    assert_isfile(wheel)


def test_source_date_epoch(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1633007882")
    wheel = make_wheel(pyproject_file=data_dir / "pep621" / "pyproject.toml", output_dir=tmp_path)
    assert_isfile(wheel)
    # Minimum value for zip timestamps is 1980-1-1
    with ZipFile(wheel, "r") as zf:
        assert zf.getinfo("module1a.py").date_time == (2022, 2, 2, 2, 2, 2)


def test_zero_timestamp(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    wheel = make_wheel(pyproject_file=data_dir / "pep621" / "pyproject.toml", output_dir=tmp_path)
    assert_isfile(wheel)
    # Minimum value for zip timestamps is 1980-1-1
    with ZipFile(wheel, "r") as zf:
        assert zf.getinfo("module1a.py").date_time == (2022, 2, 2, 2, 2, 2)


def test_data_dir(tmp_path):
    wheel = make_wheel(
        pyproject_file=data_dir / "with_data_dir" / "pyproject.toml",
        output_dir=tmp_path,
    )
    assert_isfile(wheel)
    with ZipFile(wheel, "r") as zf:
        names = zf.namelist()
        assert "data/share/man/man1/foo.1" in names
        assert "module1-1.2.dist-info/LICENSE" in names
        assert "module1-1.2.dist-info/README.rst" not in names


def unpack(path):
    z = zipfile.ZipFile(str(path))
    t = tempfile.TemporaryDirectory()
    z.extractall(t.name)
    return t


def test_wheel_module(copy_test_data):
    td = copy_test_data("module1_toml")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    expected = td / "module1-1.0-py3-none-any.whl"
    assert_isfile(wf)
    assert str(wf) == str(expected)

    with unpack(wf) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "module1-1.0.dist-info/METADATA",
            "module1-1.0.dist-info/RECORD",
            "module1-1.0.dist-info/WHEEL",
            "module1.py",
        ]


def test_editable_wheel_module(copy_test_data):
    td = copy_test_data("module1_toml")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td, editable=True)
    whl_file = td / "module1-1.0-py3-none-any.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        pth_path = Path(unpacked, "module1.pth")
        assert_isfile(pth_path)
        assert pth_path.read_text().endswith("module1.py\n")
        assert_isdir(Path(unpacked, "module1-1.0.dist-info"))


def test_editable_wheel_has_absolute_pth(copy_test_data):
    td = copy_test_data("module1_toml")
    oldcwd = os.getcwd()
    os.chdir(td)
    try:
        wf = make_wheel(pyproject_file=Path("pyproject.toml"), output_dir=td, editable=True)
        whl_file = Path("module1-1.0-py3-none-any.whl").absolute()
        assert_isfile(wf)
        assert str(wf) == str(whl_file)
        with unpack(whl_file) as unpacked:
            path_file = Path(unpacked, "module1.pth")
            check_paths(path_file, td)
            assert_isdir(Path(unpacked, "module1-1.0.dist-info"))
    finally:
        os.chdir(oldcwd)


def check_paths(path_file, test_dir):
    assert_isfile(path_file)
    for pth in path_file.read_text().splitlines(False):
        p = Path(pth)
        assert p.is_absolute()
        assert p.exists()
        assert pth.startswith(str(test_dir))


def test_wheel_package(copy_test_data):
    td = copy_test_data("package1")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    whl_file = td / "package1-0.0.1-py3-none-any.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)

    with unpack(wf) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "__init__.py",
            "data_dir/foo.sh",
            "foo.py",
            "package1-0.0.1.dist-info/METADATA",
            "package1-0.0.1.dist-info/RECORD",
            "package1-0.0.1.dist-info/WHEEL",
            "package1-0.0.1.dist-info/entry_points.txt",
            "package1/__init__.py",
            "package1/data_dir/foo.sh",
            "package1/foo.py",
            "package1/subpkg/__init__.py",
            "package1/subpkg/sp_data_dir/test.json",
            "package1/subpkg2/__init__.py",
            "subpkg/__init__.py",
            "subpkg/sp_data_dir/test.json",
            "subpkg2/__init__.py",
        ]


def test_editable_wheel_package(copy_test_data):
    td = copy_test_data("package1")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td, editable=True)
    whl_file = td / "package1-0.0.1-py3-none-any.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        pth_path = Path(unpacked, "package1.pth")
        check_paths(pth_path, td)
        assert_isdir(Path(unpacked, "package1-0.0.1.dist-info"))


def test_editable_wheel_namespace_package_editable(copy_test_data):
    td = copy_test_data("ns1-pkg")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td, editable=True)
    whl_file = td / "ns1_pkg-1.0-py3-none-any.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        pth_path = Path(unpacked, "ns1.pkg.pth")
        assert_isfile(pth_path)
        lines = pth_path.read_text().splitlines(False)
        assert lines == [str(td / "ns1")]
        assert_isdir(Path(unpacked, "ns1_pkg-1.0.dist-info"))


def test_wheel_module3_with_src_dir(copy_test_data):
    td = copy_test_data("module3")
    wf = make_wheel(
        pyproject_file=td / "pyproject.toml",
        output_dir=td / "dist",
    )
    with unpack(wf) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "module3-1.0.dist-info/LICENSE",
            "module3-1.0.dist-info/METADATA",
            "module3-1.0.dist-info/RECORD",
            "module3-1.0.dist-info/WHEEL",
            "src/module3.py",
        ]


def test_editable_wheel_module3_with_src_dir(copy_test_data):
    td = copy_test_data("module3")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td, editable=True)
    whl_file = td / "module3-1.0-py3-none-any.whl"
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        pth_path = Path(unpacked, "module3.pth")
        assert_isfile(pth_path)
        assert pth_path.read_text().strip() == str(td / "src")
        assert_isdir(Path(unpacked, "module3-1.0.dist-info"))


def test_wheel_with_src_package(copy_test_data):
    td = copy_test_data("package2")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    whl_file = td / "package2-1.0.0-py3-none-any.whl"
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        expected = [
            "package2-1.0.0.dist-info/METADATA",
            "package2-1.0.0.dist-info/RECORD",
            "package2-1.0.0.dist-info/WHEEL",
            "package2/__init__.py",
            "package2/foo.py",
        ]
        assert files == expected


def test_editable_wheel_src_package(copy_test_data):
    td = copy_test_data("package2")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td, editable=True)
    whl_file = td / "package2-1.0.0-py3-none-any.whl"
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        pth_path = Path(unpacked, "package2.pth")
        assert_isfile(pth_path)
        assert pth_path.read_text().strip() == str(td / "src")
        assert_isdir(Path(unpacked, "package2-1.0.0.dist-info"))


def test_wheel_ns_package(copy_test_data):
    td = copy_test_data("ns1-pkg")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    assert wf == td / "ns1_pkg-1.0-py3-none-any.whl"
    assert_isfile(wf)
    with unpack(wf) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "ns1/pkg/__init__.py",
            "ns1_pkg-1.0.dist-info/METADATA",
            "ns1_pkg-1.0.dist-info/RECORD",
            "ns1_pkg-1.0.dist-info/WHEEL",
        ]


def test_dist_name(copy_test_data):
    td = copy_test_data("altdistname")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    whl_file = td / "packagefoo-1.0-py3-none-any.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)

    with unpack(wf) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "package1/__init__.py",
            "package1/data_dir/foo.sh",
            "package1/foo.py",
            "package1/subpkg/__init__.py",
            "package1/subpkg/sp_data_dir/test.json",
            "package1/subpkg2/__init__.py",
            "packagefoo-1.0.dist-info/METADATA",
            "packagefoo-1.0.dist-info/RECORD",
            "packagefoo-1.0.dist-info/WHEEL",
        ]


def test_entry_points(copy_test_data):
    td = copy_test_data("entrypoints_valid")
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    whl_file = td / "package1-1.0-py3-none-any.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)
    with unpack(td / "package1-1.0-py3-none-any.whl") as td_unpack:
        entry_points = Path(td_unpack, "package1-1.0.dist-info", "entry_points.txt")
        assert_isfile(entry_points)
        cp = configparser.ConfigParser()
        cp.read(str(entry_points))
        results = {sec: cp.items(section=sec, raw=True) for sec in cp.sections()}
        expected = {
            "console_scripts": [("pkg_script", "package1:main")],
            "myplugins": [("package1", "package1:main")],
        }
        assert results == expected


def test_wheel_builder():
    # Slightly lower level interface
    with tempfile.TemporaryDirectory() as td:
        wb = WheelBuilder.from_pyproject_file(
            pyproject_file=data_dir / "package1" / "pyproject.toml"
        )
        target = wb.build(output_dir=td)

        assert zipfile.is_zipfile(target)
        assert str(target) == str(Path(td) / "package1-0.0.1-py3-none-any.whl")


@skipIf(os.name == "nt", "Windows does not preserve necessary permissions")
def test_permissions_normed(copy_test_data):
    td = copy_test_data("module1_toml")

    (td / "module1.py").chmod(0o620)
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)

    whl_file = td / "module1-1.0-py3-none-any.whl"
    assert str(wf) == str(whl_file)

    with zipfile.ZipFile(str(whl_file)) as zf:
        info = zf.getinfo("module1.py")
        perms = (info.external_attr >> 16) & 0o777
        assert perms == 0o644, oct(perms)
    whl_file.unlink()

    # This time with executable bit set
    (td / "module1.py").chmod(0o720)
    wf = make_wheel(pyproject_file=td / "pyproject.toml", output_dir=td)
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)
    with zipfile.ZipFile(str(whl_file)) as zf:
        info = zf.getinfo("module1.py")
        perms = (info.external_attr >> 16) & 0o777
        assert perms == 0o755, oct(perms)

        info = zf.getinfo("module1-1.0.dist-info/METADATA")
        perms = (info.external_attr >> 16) & 0o777
        assert perms == 0o644, oct(perms)

        info = zf.getinfo("module1-1.0.dist-info/RECORD")
        perms = (info.external_attr >> 16) & stat.S_IFREG
        assert perms


def test_compression(tmp_path):
    wf = make_wheel(
        pyproject_file=data_dir / "module1_toml" / "pyproject.toml", output_dir=tmp_path
    )
    assert_isfile(wf)
    with zipfile.ZipFile(wf) as zf:
        for name in [
            "module1.py",
            "module1-1.0.dist-info/METADATA",
        ]:
            assert zf.getinfo(name).compress_type == zipfile.ZIP_DEFLATED


def test_wheel_module_local_version_and_custom_tag(copy_test_data):
    """Test if a local version specifier is preserved in wheel filename and dist-info dir name"""
    td = copy_test_data("modulewithlocalversion")
    wf = make_wheel(
        pyproject_file=td / "pyproject.toml",
        output_dir=td,
        wheel_tag="py2.py3-none-manylinux1_x86_64",
    )

    whl_file = td / "modulewithlocalversion-1.0.dev0+test-py2.py3-none-manylinux1_x86_64.whl"
    assert_isfile(whl_file)
    assert str(wf) == str(whl_file)
    with unpack(whl_file) as unpacked:
        assert_isfile(Path(unpacked, "modulewithlocalversion.py"))
        dist_info_dir = Path(unpacked, "modulewithlocalversion-1.0.dev0+test.dist-info")
        assert_isdir(dist_info_dir)
        wheel_tags = (dist_info_dir / "WHEEL").read_text().splitlines(False)
        from flot import __version__

        expected = [
            "Wheel-Version: 1.0",
            f"Generator: flot {__version__}",
            "Root-Is-Purelib: false",
            "Tag: py2.py3-none-manylinux1_x86_64",
        ]
        assert wheel_tags == expected


def test_WheelBuilder_build_with_scripts(
    copy_test_data,
    tmp_path,
):
    td = copy_test_data("scripts")
    builder = WheelBuilder.from_pyproject_file(td / "not-py-project.foo")
    wd = builder.build(tmp_path)

    with unpack(wd) as unpacked:
        files = sorted(
            str(p.relative_to(unpacked)) for p in Path(unpacked).glob("**/*") if p.is_file()
        )
        assert files == [
            "deep/nested/foo.py",
            "module3-1.0.dist-info/LICENSE",
            "module3-1.0.dist-info/METADATA",
            "module3-1.0.dist-info/RECORD",
            "module3-1.0.dist-info/WHEEL",
            "module3.py",
            "module4.py",
            "somenewfile-wheel.txt",
        ]

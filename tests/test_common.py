#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

from pathlib import Path

import pytest

from flot.common import FilePatterns
from flot.common import InvalidVersion
from flot.common import NoVersionError
from flot.common import check_version
from flot.common import iter_files
from flot.common import normalize_file_permissions

data_dir = Path(__file__).parent / "data"


def test_version_raise():
    with pytest.raises(InvalidVersion):
        check_version("a.1.0.beta0")

    with pytest.raises(InvalidVersion):
        check_version("3!")

    with pytest.raises(InvalidVersion):
        check_version((1, 2))

    with pytest.raises(NoVersionError):
        check_version(None)

    assert check_version("4.1.0beta1") == "4.1.0b1"
    assert check_version("v1.2") == "1.2"


def test_normalize_file_permissions():
    assert normalize_file_permissions(0o100664) == 0o100644  # regular file
    assert normalize_file_permissions(0o40775) == 0o40755  # directory


def test_iter_files_can_iter_dir(get_test_data):
    test_dir = get_test_data("module3")
    expected = ["LICENSE", "pyproject.toml", "src/module3.py"]
    results = [str(Path(f).relative_to(test_dir)) for f in iter_files(test_dir)]
    assert results == expected


def test_iter_files_can_iter_file(get_test_data):
    test_dir = get_test_data("module3")
    expected = ["LICENSE", "pyproject.toml", "src/module3.py"]
    results = [str(Path(f).relative_to(test_dir)) for f in iter_files(test_dir)]
    assert results == expected


def test_iter_files_ignores_pycache_and_pyc(copy_test_data):
    test_dir = Path(copy_test_data("module3"))

    pyc1 = test_dir / "python1.pyc"
    with pyc1.open("w") as f:
        f.write("")

    pycache = test_dir / "__pycache__"
    pycache.mkdir()

    pyc2 = pycache / "python2.pyc"
    with pyc2.open("w") as f:
        f.write("")

    expected = ["LICENSE", "pyproject.toml", "src/module3.py"]
    results = [str(Path(f).relative_to(test_dir)) for f in iter_files(test_dir)]
    assert results == expected


def test_apply_includes_excludes_with_simple_file_include(get_test_data):
    base_dir = get_test_data("module3")
    files = list(iter_files(base_dir))
    rel_files = [str(Path(f).relative_to(base_dir)) for f in files]
    assert rel_files == ["LICENSE", "pyproject.toml", "src/module3.py"]

    include_patterns = FilePatterns(patterns=["pyproject.toml"], base_dir=base_dir)
    assert list(map(str, include_patterns.files)) == ["pyproject.toml"]

    results = [
        str(p)
        for p in FilePatterns.apply_includes_excludes(
            base_dir=base_dir,
            files=files,
            include_patterns=include_patterns,
            relative_paths=True,
        )
    ]
    expected = ["pyproject.toml"]
    assert results == expected


def test_apply_includes_excludes_with_file_includes_and_excludes(get_test_data):
    base_dir = get_test_data("module4")
    files = list(iter_files(base_dir))
    rel_files = [str(Path(f).relative_to(base_dir)) for f in files]
    assert rel_files == [
        "LICENSE",
        "pyproject.toml",
        "src/module3.py",
        "src/module4.py",
    ]

    include_patterns = FilePatterns(
        patterns=["pyproject.toml", "src/**/*"], base_dir=base_dir
    )
    expected = {"pyproject.toml", "src/module3.py", "src/module4.py"}
    assert include_patterns.files == expected

    exclude_patterns = FilePatterns(patterns=["src/module3.py"], base_dir=base_dir)
    assert exclude_patterns.files == {"src/module3.py"}

    results = [
        str(p)
        for p in FilePatterns.apply_includes_excludes(
            base_dir=base_dir,
            files=files,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            relative_paths=True,
        )
    ]
    expected = ["pyproject.toml", "src/module4.py"]
    assert results == expected


def test_apply_includes_excludes_with_nested_file_includes_and_excludes(get_test_data):
    base_dir = get_test_data("module5")
    files = list(iter_files(base_dir))
    rel_files = [str(Path(f).relative_to(base_dir)) for f in files]
    assert rel_files == [
        "LICENSE",
        "pyproject.toml",
        "src/deep/nested/foo.py",
        "src/module3.py",
        "src/module4.py",
    ]

    include_patterns = FilePatterns(
        patterns=["pyproject.toml", "src/**/*"], base_dir=base_dir
    )
    expected = {
        "src/module4.py",
        "pyproject.toml",
        "src/deep/nested/foo.py",
        "src/module3.py",
    }
    assert include_patterns.files == expected

    exclude_patterns = FilePatterns(
        patterns=["src/module3.py", "src/deep/**/*"], base_dir=base_dir
    )
    assert exclude_patterns.files == {"src/module3.py", "src/deep/nested/foo.py"}

    results = [
        str(p)
        for p in FilePatterns.apply_includes_excludes(
            base_dir=base_dir,
            files=files,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            relative_paths=True,
        )
    ]
    expected = ["pyproject.toml", "src/module4.py"]
    assert results == expected

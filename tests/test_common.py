#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

from pathlib import Path

import pytest

from flot.common import FileSelector
from flot.common import InvalidVersion
from flot.common import NoVersionError
from flot.common import check_version
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


def test_FileSelector_ignores_pycache_and_pyc(copy_test_data):
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
    fs = FileSelector(
        base_dir=test_dir,
        includes=["**/*"],
    )
    results = [str(frel) for _fabs, frel in fs.files]
    assert results == expected


def test_FileSelector_honors_includes(get_test_data):
    base_dir = get_test_data("module3")
    fs = FileSelector(
        base_dir=base_dir,
        includes=["pyproject.toml"],
    )
    results = [str(frel) for _fabs, frel in fs.files]
    assert results == ["pyproject.toml"]


def test_FileSelector_honors_includes_and_excludes(get_test_data):
    base_dir = get_test_data("module4")
    fs = FileSelector(
        base_dir=base_dir,
        includes=["pyproject.toml", "src/**/*"],
    )
    expected = ["pyproject.toml", "src/module3.py", "src/module4.py"]
    results = [str(frel) for _fabs, frel in fs.files]
    assert results == expected

    fs = FileSelector(
        base_dir=base_dir,
        includes=["pyproject.toml", "src/**/*"],
        excludes=["src/module3.py"],
    )
    results = [str(frel) for _fabs, frel in fs.files]
    expected = ["pyproject.toml", "src/module4.py"]
    assert results == expected


def test_FileSelector_honors_includes_excludes_with_nested_file_tree(get_test_data):
    base_dir = get_test_data("module5")

    fs = FileSelector(
        base_dir=base_dir,
        includes=["pyproject.toml", "src/**/*"],
    )
    results = [str(frel) for _fabs, frel in fs.files]
    expected = [
        "pyproject.toml",
        "src/deep/nested/foo.py",
        "src/module3.py",
        "src/module4.py",
    ]
    assert results == expected

    fs = FileSelector(
        base_dir=base_dir,
        includes=["pyproject.toml", "src/**/*"],
        excludes=["src/module3.py", "src/deep/**/*"],
    )

    results = [str(frel) for _fabs, frel in fs.files]
    expected = ["pyproject.toml", "src/module4.py"]
    assert results == expected

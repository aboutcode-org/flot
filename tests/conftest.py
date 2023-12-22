#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

from pathlib import Path
from shutil import copytree

import pytest

data_dir = Path(__file__).parent / "data"


@pytest.fixture
def copy_test_data(tmp_path):
    """Copy a subdirectory from the data dir to a temp dir"""

    def copy(dirname):
        dst = tmp_path / dirname
        copytree(str(data_dir / dirname), str(dst))
        return dst

    return copy


@pytest.fixture
def get_test_data():
    """Return a Path in the data dir"""

    def _get_path(path):
        return str(data_dir / path)

    return _get_path

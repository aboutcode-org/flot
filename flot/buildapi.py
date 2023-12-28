#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import io
import logging
import os
import os.path as osp

from .common import Metadata
from .common import dist_info_name
from .common import write_entry_points
from .config import read_pyproject_file
from .sdist import make_sdist
from .wheel import _write_WHEEL_file
from .wheel import make_wheel

log = logging.getLogger(__name__)

"""PEP-517 compliant buildsystem API"""


# We have no extra building reuirements and to build sdist, wheel or editable
# Requirements to build an editable are the same as for a wheel
def get_requires_for_build_wheel(config_settings=None):
    return []


get_requires_for_build_sdist = get_requires_for_build_wheel
get_requires_for_build_editable = get_requires_for_build_wheel


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    """Creates {metadata_directory}/foo-1.2.dist-info"""
    config_settings = config_settings or {}
    pyproject_file = config_settings.get("--pyproject")
    wheel_tag = config_settings.get("--wheel-tag") or "py3-any-none"

    project_info = read_pyproject_file(pyproject_file)
    metadata = Metadata(project_info.metadata)

    dist_info_dir = osp.join(metadata_directory, dist_info_name(metadata.name, metadata.version))
    os.mkdir(dist_info_dir)

    if project_info.entrypoints:
        with io.open(osp.join(dist_info_dir, "entry_points.txt"), "w", encoding="utf-8") as f:
            write_entry_points(project_info.entrypoints, f)

    with io.open(osp.join(dist_info_dir, "WHEEL"), "w", encoding="utf-8") as f:
        _write_WHEEL_file(f, wheel_tag=wheel_tag)

    with io.open(osp.join(dist_info_dir, "METADATA"), "w", encoding="utf-8") as f:
        metadata.write_metadata_file(f)

    return osp.basename(dist_info_dir)


# Metadata for editable are the same as for a wheel
prepare_metadata_for_build_editable = prepare_metadata_for_build_wheel


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    config_settings = config_settings or {}
    pyproject_file = config_settings.get("--pyproject")
    wheel_tag = config_settings.get("--wheel-tag")

    wheel_file = make_wheel(
        pyproject_file=pyproject_file,
        output_dir=wheel_directory,
        wheel_tag=wheel_tag,
    )
    return wheel_file.name


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    config_settings = config_settings or {}
    pyproject_file = config_settings.get("--pyproject")
    wheel_tag = config_settings.get("--wheel-tag")

    wheel_file = make_wheel(
        pyproject_file=pyproject_file,
        output_dir=wheel_directory,
        wheel_tag=wheel_tag,
        editable=True,
    )
    return wheel_file.name


def build_sdist(sdist_directory, config_settings=None):
    config_settings = config_settings or {}
    pyproject_file = config_settings.get("--pyproject")

    sdist_file = make_sdist(
        pyproject_file=pyproject_file,
        output_dir=sdist_directory,
    )
    return sdist_file.name

#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import hashlib
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from subprocess import check_output

from . import versionno

log = logging.getLogger(__name__)


# For the timestamps, default to 2022-02-02T02:02:02 (UTC)
# This makes the build reproducible. Use the SOURCE_DATE_EPOCH env var with a
# UTC Unix timestamp for an alternative date.

_DT = datetime.fromisoformat("2022-02-02T02:02:02")
FLOT_EPOCH_TIMESTAMP = int(os.environ.get("SOURCE_DATE_EPOCH") or _DT.timestamp())
_DT = datetime.fromtimestamp(FLOT_EPOCH_TIMESTAMP)
# zipfile expects a 6-tuple: neither a Unix timestamp nor datetime object.
FLOT_ZIP_TIME = (
    _DT.year,
    _DT.month,
    _DT.day,
    _DT.hour,
    _DT.minute,
    _DT.second,
)


class FileSelector:
    """
    Compute a set of file Path inclusion or exclusion patterns relative to
    base_dir
    """

    def __init__(
        self,
        base_dir,
        includes,
        excludes=None,
        label=None,
    ):
        self.base_dir = base_dir = Path(base_dir).absolute()

        log.debug(
            f"FileSelector: includes: {includes!r}, "
            f"excludes: {excludes!r}, base_dir: {base_dir!r}"
        )

        if not isinstance(includes, (list, tuple)):
            raise Exception(
                f"Invalid includes patterns: not a list: {type(includes)!r} - {includes!r}"
            )
        self.includes = tuple(includes)

        if excludes:
            if not isinstance(excludes, (list, tuple)):
                raise Exception(
                    f"Invalid excludes patterns: not a list: {type(excludes)!r} - {excludes!r}"
                )
            self.excludes = tuple(excludes)
        else:
            self.excludes = tuple()

        self.label = label or ""

    @property
    def files(self):
        selected_files = set()

        log.info(f"Selecting files for {self.label!r}")

        for pattern in self.includes:
            # Note that a trailing / in Path.glob will return only dirs in
            # Python 3.11 and up
            # pattern = pattern.rstrip("/")
            try:
                selected_files.update(self.base_dir.glob(pattern))
                log.info(
                    f"  Includes pattern: {pattern!r}: " f"{len(selected_files)} files to include"
                )
            except Exception as e:
                raise Exception(f"Invalid pattern: {pattern!r}") from e

        for pattern in self.excludes:
            try:
                selected_files.difference_update(self.base_dir.glob(pattern))
                log.info(
                    f"  Excludes pattern: {pattern!r}: " f"{len(selected_files)} files to exclude"
                )
            except Exception as e:
                raise Exception(f"Invalid pattern: {pattern!r}") from e

        # list of tuples of (absolute Path, relative Path)
        return sorted(
            (path, path.relative_to(self.base_dir))
            for path in selected_files
            if not path.is_dir()
            # TODO: we could also ignore ~ editor/swap files and pyo
            and path.suffix != ".pyc"
        )


class NoVersionError(ValueError):
    pass


class InvalidVersion(ValueError):
    pass


def check_version(version):
    """
    Check whether a given version string match PEP 440, and do normalisation.

    Raise InvalidVersion/NoVersionError with relevant information if
    version is invalid.

    Log a warning if the version is not canonical with respect to PEP 440.

    Returns the version in canonical PEP 440 format.
    """
    if not version:
        raise NoVersionError(
            "Cannot package module without a version string. "
            'Please define a `__version__ = "x.y.z"` in your module.'
        )
    if not isinstance(version, str):
        raise InvalidVersion("__version__ must be a string, not {}.".format(type(version)))

    # Import here to avoid circular import
    version = versionno.normalize_version(version)

    return version


def parse_entry_point(ep):
    """Check and parse a 'package.module:func' style entry point specification.

    Returns (modulename, funcname)
    """
    if ":" not in ep:
        raise ValueError("Invalid entry point (no ':'): %r" % ep)
    mod, func = ep.split(":")

    for piece in func.split("."):
        if not piece.isidentifier():
            raise ValueError("Invalid entry point: %r is not an identifier" % piece)
    for piece in mod.split("."):
        if not piece.isidentifier():
            raise ValueError("Invalid entry point: %r is not a module path" % piece)

    return mod, func


def write_entry_points(d, fp):
    """Write entry_points.txt from a two-level dict

    Sorts on keys to ensure results are reproducible.
    """
    for group_name in sorted(d):
        fp.write("[{}]\n".format(group_name))
        group = d[group_name]
        for name in sorted(group):
            val = group[name]
            fp.write("{}={}\n".format(name, val))
        fp.write("\n")


def hash_file(path, algorithm="sha256"):
    with open(path, "rb") as f:
        h = hashlib.new(algorithm, f.read())
    return h.hexdigest()


def normalize_file_permissions(st_mode):
    """Normalize the permission bits in the st_mode field from stat to 644/755

    Popular VCSs only track whether a file is executable or not. The exact
    permissions can vary on systems with different umasks. Normalising
    to 644 (non executable) or 755 (executable) makes builds more reproducible.
    """
    # Set 644 permissions, leaving higher bits of st_mode unchanged
    new_mode = (st_mode | 0o644) & ~0o133
    if st_mode & 0o100:
        new_mode |= 0o111  # Executable: 644 -> 755
    return new_mode


class Metadata:
    summary = None
    home_page = None
    author = None
    author_email = None
    maintainer = None
    maintainer_email = None
    license = None
    description = None
    keywords = None
    download_url = None
    requires_python = None
    description_content_type = None

    platform = ()
    supported_platform = ()
    classifiers = ()
    requires = ()
    obsoletes = ()
    project_urls = ()
    provides_dist = ()
    requires_dist = ()
    obsoletes_dist = ()
    requires_external = ()
    provides_extra = ()

    metadata_version = "2.1"

    def __init__(self, data):
        data = data.copy()
        self.name = data.pop("name")
        self.version = data.pop("version")

        for k, v in data.items():
            assert hasattr(self, k), "data does not have attribute '{}'".format(k)
            setattr(self, k, v)

    def _normalise_name(self, n):
        return n.lower().replace("-", "_")

    def write_metadata_file(self, fp):
        """Write out metadata in the email headers format"""
        fields = [
            "Metadata-Version",
            "Name",
            "Version",
        ]
        optional_fields = [
            "Summary",
            "Home-page",
            "License",
            "Keywords",
            "Author",
            "Author-email",
            "Maintainer",
            "Maintainer-email",
            "Requires-Python",
            "Description-Content-Type",
        ]

        for field in fields:
            value = getattr(self, self._normalise_name(field))
            fp.write("{}: {}\n".format(field, value))

        for field in optional_fields:
            value = getattr(self, self._normalise_name(field))
            if value is not None:
                # TODO: verify which fields can be multiline
                # The spec has multiline examples for Author, Maintainer &
                # License (& Description, but we put that in the body)
                # Indent following lines with 8 spaces:
                value = "\n        ".join(value.splitlines())
                fp.write("{}: {}\n".format(field, value))

        for clsfr in self.classifiers:
            fp.write("Classifier: {}\n".format(clsfr))

        for req in self.requires_dist:
            fp.write("Requires-Dist: {}\n".format(req))

        for url in self.project_urls:
            fp.write("Project-URL: {}\n".format(url))

        for extra in self.provides_extra:
            fp.write("Provides-Extra: {}\n".format(extra))

        if self.description is not None:
            fp.write("\n" + self.description + "\n")


def normalize_dist_name(name: str, version: str) -> str:
    """Normalizes a name and a PEP 440 version

    The resulting string is valid as dist-info folder name
    and as first part of a wheel filename

    See https://packaging.python.org/specifications/binary-distribution-format/#escaping-and-unicode
    """
    normalized_name = re.sub(r"[-_.]+", "_", name, flags=re.UNICODE).lower()
    assert check_version(version) == version
    assert "-" not in version, "Normalized versions can’t have dashes"
    return "{}-{}".format(normalized_name, version)


def dist_info_name(distribution, version):
    """Get the correct name of the .dist-info dir"""
    return normalize_dist_name(distribution, version) + ".dist-info"


def run_scripts(pyproject_file, scripts=()):
    """
    Support running arbitrary build scripts at the start of a wheel or sdist
    build.

    The scripts are simple Python scripts that accept a single argument: the
    absolute path to the pyproject.toml file used to run the build.

    They must be available in a location realtive to the pyproject.toml file.

    Scripts may have requirements for extra Python package to use at build time.
    These should be added to the  ``[build-system]`` table requires section.
    """
    for abs_path, _rel_path in scripts:
        script = str(abs_path)
        log.info(f"Running script: {sys.executable} {abs_path} {pyproject_file}")
        check_output([sys.executable, script, pyproject_file])

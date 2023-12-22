#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import hashlib
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

from .versionno import normalize_version


class FilePatterns:
    """
    Compute a set of file Path inclusion or exclusion patterns relative to
    base_dir
    """

    def __init__(self, patterns, base_dir):
        self.base_dir = Path(base_dir).absolute()
        self.files = set()

        log.debug(f"FilePatterns: patterns: {patterns} base_dir: {base_dir}")

        for pattern in patterns:
            # Always remove trailing / as Path.rglob will return only dirs in
            # Python 3.11 and up with this
            pattern = pattern.rstrip("/")
            for path in sorted(self.base_dir.glob(pattern)):
                if path.is_dir():
                    continue
                rel_path = str(path.relative_to(base_dir))
                log.debug(f"FilePatterns.add: {rel_path}")
                self.files.add(rel_path)

    def match_file(self, rel_path):
        log.debug(
            f"match_file: {rel_path} is matched: {rel_path in self.files} in {self.files!r}"
        )
        return str(rel_path) in self.files

    @classmethod
    def apply_includes_excludes(
        cls,
        base_dir,
        files,
        include_patterns,
        exclude_patterns=None,
        relative_paths=False,
    ):
        """
        Return a sorted list of file Path objects filtered from
        applying include and exclude patterns.
        """
        if not exclude_patterns:
            exclude_patterns = cls([], base_dir=base_dir)

        base_dir = Path(base_dir)
        all_files = [Path(f).relative_to(base_dir) for f in files]
        paths = set()
        for path in all_files:
            if include_patterns.match_file(path) and not exclude_patterns.match_file(
                path
            ):
                if not relative_paths:
                    path = base_dir / path
                paths.add(path)
        return sorted(paths)


class FileSelector:
    """A mixin for builders to help select files"""

    def select_files(self):
        """
        Yield tuple of (absolute Path, relative Path) for files to include in
        all distributions (wheel and sdist).
        """
        include_patterns = self.include_patterns
        exclude_patterns = self.exclude_patterns
        return self._select_files(self.base_dir, include_patterns, exclude_patterns)

    def select_extra_sdist_files(self):
        """
        Yield tuple of (absolute Path, relative Path) for files to include as
        extra in the sdist distribution.
        """
        include_patterns = self.sdist_extra_include_patterns
        exclude_patterns = self.sdist_extra_exclude_patterns
        return self._select_files(self.base_dir, include_patterns, exclude_patterns)

    def select_metafiles(self):
        """
        Yield tuple of (absolute Path, relative Path) for files to include in
        a wheel metadata. Also include in an sdist.
        """
        include_patterns = self.metadata_file_patterns
        return self._select_files(self.base_dir, include_patterns)

    @classmethod
    def _select_files(cls, base_dir, include_patterns, exclude_patterns=None):
        """
        Yield tuple of (absolute Path, relative Path) for files to include as
        extra in the sdist distribution.
        """
        log.debug(f"_select_files: project_dir: {base_dir}")
        files = iter_files(base_dir)
        for abs_path in FilePatterns.apply_includes_excludes(
            base_dir=base_dir,
            files=files,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        ):
            yield abs_path, abs_path.relative_to(base_dir)


def iter_files(base_dir: Path):
    """Iterate over the files contained in this base_dir Path.

    Yields absolute paths - caller may want to make them relative.
    Excludes any __pycache__ and *.pyc files.
    """
    base_dir = Path(base_dir)
    if base_dir.is_file():
        yield base_dir
    else:
        yield from (
            p
            for p in sorted(base_dir.rglob("*"))
            if p.is_file() and p.name != "__pycache__" and p.suffix != ".pyc"
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
        raise InvalidVersion(
            "__version__ must be a string, not {}.".format(type(version))
        )

    # Import here to avoid circular import
    version = normalize_version(version)

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

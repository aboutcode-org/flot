#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import contextlib
import hashlib
import io
import logging
import os
import stat
from base64 import urlsafe_b64encode
from datetime import datetime
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile
from zipfile import ZipInfo

from . import common

log = logging.getLogger(__name__)


def _write_WHEEL_file(f, wheel_tag=None):
    from flot import __version__

    wheel_tag = wheel_tag or "py3-none-any"
    is_pure_lib = "true" if wheel_tag == "py3-none-any" else "false"

    wheel_file_template = f"""\
Wheel-Version: 1.0
Generator: flot {__version__}
Root-Is-Purelib: {is_pure_lib}
Tag: {wheel_tag}
"""
    f.write(wheel_file_template)


def _set_zinfo_mode(zinfo, mode):
    # Set the bits for the mode
    zinfo.external_attr = mode << 16


def zip_timestamp_from_env() -> Optional[tuple]:
    """Prepare a timestamp from $SOURCE_DATE_EPOCH, if set"""
    try:
        # If SOURCE_DATE_EPOCH is set (e.g. by Debian), it's used for
        # timestamps inside the zip file.
        d = datetime.utcfromtimestamp(int(os.environ["SOURCE_DATE_EPOCH"]))
    except (KeyError, ValueError):
        # Otherwise, we'll use the mtime of files, and generated files will
        # default to 2016-1-1 00:00:00
        return None

    if d.year >= 1980:
        log.info("Zip timestamps will be from SOURCE_DATE_EPOCH: %s", d)
        # zipfile expects a 6-tuple, not a datetime object
        return d.year, d.month, d.day, d.hour, d.minute, d.second
    else:
        log.info("SOURCE_DATE_EPOCH is below the minimum for zip file timestamps")
        log.info("Zip timestamps will be 1980-01-01 00:00:00")
        return 1980, 1, 1, 0, 0, 0


class WheelBuilder(common.FileSelector):
    def __init__(
        self,
        pyproject_file,
        metadata,
        entrypoints,
        includes=(),
        excludes=(),
        path_prefixes_to_strip=(),
        editable_paths=(),
        metadata_files=(),
        wheel_tag=None,
    ):
        """
        Build a wheel for the files include/exclude patterns provided
        """
        log.debug(f"WheelBuilder: {pyproject_file}")
        self.pyproject_file = Path(pyproject_file).absolute()
        self.base_dir = self.pyproject_file.parent
        self.metadata = metadata
        self.entrypoints = entrypoints

        self.include_patterns = common.FilePatterns(
            patterns=includes, base_dir=self.base_dir
        )
        self.exclude_patterns = common.FilePatterns(
            patterns=excludes, base_dir=self.base_dir
        )
        self.path_prefixes_to_strip = path_prefixes_to_strip

        if not editable_paths:
            editable_paths = ["."]

        self.editable_paths = editable_paths or []

        # this is the only implict addition that is too easily overseen
        if not metadata_files:
            metadata_files = (
                "*LICEN[SC]E*",
                "*COPYING*",
                "*COPYIRIGHT*",
            )
        self.metadata_file_patterns = common.FilePatterns(
            patterns=metadata_files, base_dir=self.base_dir
        )

        self.records = []
        self.source_time_stamp = zip_timestamp_from_env()

        self.wheel_tag = wheel_tag or "py3-none-any"
        self.wheel_zip = None

    @classmethod
    def from_pyproject_file(
        cls,
        pyproject_file=None,
        wheel_tag=None,
    ):
        """
        Create a wheel in target_dir, default: <pyproject file parent>/dist
        from an arbitrary pyproject.toml file path, default: "pyproject.toml".
        Use an optional wheel tag, default: "py3-none-any"
        """
        pyproject_file = pyproject_file or "pyproject.toml"
        wheel_tag = wheel_tag or "py3-none-any"

        from .config import read_pyproject_file

        pyproject_file = Path(pyproject_file).absolute()
        project_info = read_pyproject_file(pyproject_file)

        return cls(
            pyproject_file=pyproject_file,
            metadata=common.Metadata(project_info.metadata),
            entrypoints=project_info.entrypoints,
            includes=project_info.includes,
            excludes=project_info.excludes,
            path_prefixes_to_strip=project_info.wheel_path_prefixes_to_strip,
            editable_paths=project_info.editable_paths,
            metadata_files=project_info.metadata_files,
            wheel_tag=wheel_tag,
        )

    @property
    def wheel_filename(self):
        dist_name = common.normalize_dist_name(
            self.metadata.name, self.metadata.version
        )
        return f"{dist_name}-{self.wheel_tag}.whl"

    def build(self, output_dir=None, editable=False):
        """
        Build wheel and return wheel file path.
        """
        output_dir = (
            output_dir and Path(output_dir) or Path(self.pyproject_file.parent) / "dist"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        target = output_dir / self.wheel_filename

        with ZipFile(target, "w", compression=ZIP_DEFLATED) as self.wheel_zip:
            if editable:
                self.add_editable_pth_file()
            else:
                self.add_files()
            self.write_metadata()
            self.write_record()
        return target

    def add_files(self):
        log.info("Copying selected file(s) to wheel")
        prefixes = self.path_prefixes_to_strip
        for abs_path, rel_path in self.select_files():
            rel_path = strip_prefixes(rel_path, prefixes)
            self._add_file(abs_path, rel_path)

    def add_editable_pth_file(self):
        """
        Write a .pth path file in an editable wheel using configured editable_paths.
        """
        base_dir = self.base_dir.absolute()
        with self._write_to_zip(self.metadata.name + ".pth") as pth_file:
            # log.debug(f"writing editable_path: {base_dir}")
            # pth_file.write(str(base_dir) + "\n")
            for rel_path in self.editable_paths:
                log.debug(f"writing editable_path: {base_dir / rel_path}")
                pth_file.write(str(base_dir / rel_path) + "\n")

    @property
    def dist_info_dir(self):
        return common.dist_info_name(self.metadata.name, self.metadata.version)

    def _add_file(self, abs_path, rel_path):
        log.debug(f"Adding {abs_path!r} to zip file as {rel_path!r}")
        abs_path, rel_path = str(abs_path), str(rel_path)
        if os.sep != "/":
            # We always want to have /-separated paths in the zip file and in
            # RECORD
            rel_path = rel_path.replace(os.sep, "/")

        zinfo = ZipInfo.from_file(filename=abs_path, arcname=rel_path)
        if self.source_time_stamp:
            # Set timestamps in zipfile for reproducible build
            zinfo.date_time = self.source_time_stamp

        # Normalize permission bits to either 755 (executable) or 644
        st_mode = os.stat(abs_path).st_mode
        new_mode = common.normalize_file_permissions(st_mode)
        _set_zinfo_mode(zinfo, new_mode & 0xFFFF)  # Unix attributes

        if stat.S_ISDIR(st_mode):
            zinfo.external_attr |= 0x10  # MS-DOS directory flag

        zinfo.compress_type = ZIP_DEFLATED

        hashsum = hashlib.sha256()
        with open(abs_path, "rb") as src, self.wheel_zip.open(zinfo, "w") as dst:
            while True:
                buf = src.read(1024 * 8)
                if not buf:
                    break
                hashsum.update(buf)
                dst.write(buf)

        # keep for RECORDS
        size = os.stat(abs_path).st_size
        hash_digest = urlsafe_b64encode(hashsum.digest()).decode("ascii").rstrip("=")
        self.records.append((rel_path, hash_digest, size))

    @contextlib.contextmanager
    def _write_to_zip(self, rel_path, mode=0o644):
        sio = io.StringIO()
        yield sio

        log.debug("Writing data to %s in zip file", rel_path)
        # The default is a fixed timestamp rather than the current time, so
        # that building a wheel twice on the same computer can automatically
        # give you the exact same result.
        date_time = self.source_time_stamp or (2016, 1, 1, 0, 0, 0)
        zi = ZipInfo(rel_path, date_time)
        # Also sets bit 0x8000 for "regular file" (S_IFREG)
        _set_zinfo_mode(zi, mode | stat.S_IFREG)
        b = sio.getvalue().encode("utf-8")
        hashsum = hashlib.sha256(b)
        hash_digest = urlsafe_b64encode(hashsum.digest()).decode("ascii").rstrip("=")
        self.wheel_zip.writestr(zi, b, compress_type=ZIP_DEFLATED)
        self.records.append((rel_path, hash_digest, len(b)))

    def write_metadata(self):
        log.info("Writing metadata files")

        if self.entrypoints:
            with self._write_to_zip(self.dist_info_dir + "/entry_points.txt") as f:
                common.write_entry_points(self.entrypoints, f)

        with self._write_to_zip(self.dist_info_dir + "/WHEEL") as f:
            _write_WHEEL_file(f, wheel_tag=self.wheel_tag)

        with self._write_to_zip(self.dist_info_dir + "/METADATA") as f:
            self.metadata.write_metadata_file(f)

        # add all metadata files as-is to the root of the wheel dist-info dir
        for abs_meta, rel_meta in self.select_metafiles():
            # metadata files go directly in the dist_info directory, not in subdirs
            self._add_file(abs_meta, f"{self.dist_info_dir}/{rel_meta.name}")

    def write_record(self):
        log.info("Writing the record of files")
        # Write a record of the files in the wheel
        with self._write_to_zip(self.dist_info_dir + "/RECORD") as f:
            for path, hsh, size in self.records:
                f.write("{},sha256={},{}\n".format(path, hsh, size))
            # RECORD itself is recorded with no hash or size
            f.write(self.dist_info_dir + "/RECORD,,\n")


def strip_prefixes(rel_path, prefixes):
    """
    Return a ``rel_path`` relative path  string stripped from the first found
    prefix of a list of ``prefixes`` path strings where rel_path starts with
    this prefix.
    Return the path unchanged if it has is no matching prefix.

    For example::
    >>> assert strip_prefixes("src/foo.py", ["lib", "src"]) == "foo.py"
    True
    >>> assert strip_prefixes("src/lib/foo.py", ["lib", "src"]) == "lib/foo.py"
    True
    >>> assert strip_prefixes("src/lib/foo.py", ["lib"]) == "src/lib/foo.py"
    True
    >>> assert strip_prefixes("foo.py", ["lib"]) == "foo.py"
    True
    >>> assert strip_prefixes("foo.py", []) == "foo.py"
    True
    """
    rel_path = str(rel_path)
    for prefix in prefixes:
        if rel_path.startswith(prefix):
            return rel_path.replace(prefix, "", 1).lstrip("/")
    return rel_path


def make_wheel(
    pyproject_file=None,
    output_dir=None,
    wheel_tag=None,
    editable=False,
):
    """
    Make a wheel, return the path.
    """
    builder = WheelBuilder.from_pyproject_file(
        pyproject_file=pyproject_file,
        wheel_tag=wheel_tag,
    )
    wheel = builder.build(output_dir=output_dir, editable=editable)
    log.info(f"Built wheel: {wheel}")
    return wheel

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
from pathlib import Path
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile
from zipfile import ZipInfo

from . import common

log = logging.getLogger(__name__)

WELL_KNOWN_WHEEL_METADATA_FILES = set(
    [
        "direct_url.json",
        "entry_points.txt",
        "INSTALLER",
        "METADATA",
        "RECORD",
        "REQUESTED",
        "WHEEL",
    ]
)


def make_wheel(
    pyproject_file=None,
    output_dir=None,
    wheel_tag=None,
    editable=False,
):
    """
    Make a wheel, return the built archive path.
    """
    builder = WheelBuilder.from_pyproject_file(
        pyproject_file=pyproject_file,
        wheel_tag=wheel_tag,
    )
    wheel = builder.build(output_dir=output_dir, editable=editable)
    log.info(f"Built wheel: {wheel}")
    return wheel


class WheelBuilder:
    def __init__(
        self,
        pyproject_file,
        metadata,
        entrypoints,
        includes=(),
        excludes=(),
        metadata_files=(),
        wheel_scripts=(),
        path_prefixes_to_strip=(),
        editable_paths=(),
        wheel_tag=None,
    ):
        log.debug(f"WheelBuilder: {pyproject_file}")
        pyproject_file = pyproject_file or "pyproject.toml"
        self.pyproject_file = Path(pyproject_file).absolute()
        self.base_dir = self.pyproject_file.parent
        self.metadata = metadata
        self.entrypoints = entrypoints

        self.selected_files = common.FileSelector(
            base_dir=self.base_dir,
            includes=includes,
            excludes=excludes,
            label="base includes/excludes",
        )

        self.selected_metadata_files = common.FileSelector(
            includes=metadata_files,
            base_dir=self.base_dir,
            label="metadata files",
        )

        self.wheel_scripts = common.FileSelector(
            includes=wheel_scripts,
            base_dir=self.base_dir,
            label="wheel scripts",
        )

        self.path_prefixes_to_strip = path_prefixes_to_strip

        if not editable_paths:
            editable_paths = ["."]

        self.editable_paths = editable_paths or []

        self.records = []

        self.wheel_tag = wheel_tag or "py3-none-any"
        self.wheel_zip = None

    @classmethod
    def from_pyproject_file(
        cls,
        pyproject_file=None,
        # TODO: may be this should be only a build arg
        wheel_tag=None,
    ):
        """
        Create a wheel in target_dir, default: <pyproject file parent>/dist
        from an arbitrary pyproject.toml file path, default: "pyproject.toml".
        Use an optional wheel tag, default: "py3-none-any"
        """
        from .config import read_pyproject_file

        pyproject_file = pyproject_file or "pyproject.toml"
        pyproject_file = Path(pyproject_file).absolute()
        project_info = read_pyproject_file(pyproject_file)

        return cls(
            pyproject_file=pyproject_file,
            metadata=common.Metadata(project_info.metadata),
            entrypoints=project_info.entrypoints,
            includes=project_info.includes,
            excludes=project_info.excludes,
            metadata_files=project_info.metadata_files,
            path_prefixes_to_strip=project_info.wheel_path_prefixes_to_strip,
            editable_paths=project_info.editable_paths,
            wheel_tag=wheel_tag or "py3-none-any",
            wheel_scripts=project_info.wheel_scripts,
        )

    @property
    def wheel_filename(self):
        dist_name = common.normalize_dist_name(self.metadata.name, self.metadata.version)
        return f"{dist_name}-{self.wheel_tag}.whl"

    def build(self, output_dir=None, editable=False):
        """
        Build wheel and return wheel file path.
        """
        common.run_scripts(self.pyproject_file, self.wheel_scripts.files)

        output_dir = output_dir and Path(output_dir) or Path(self.pyproject_file.parent) / "dist"
        output_dir.mkdir(parents=True, exist_ok=True)

        target = output_dir / self.wheel_filename

        with ZipFile(target, "w", compression=ZIP_DEFLATED) as self.wheel_zip:
            if editable:
                self.add_editable_pth_file()
            else:
                log.debug(f"WheelBuilder.build: adding files")
                self.add_files()
                log.debug(f"WheelBuilder.build: done adding files")
            self.write_metadata()
            self.write_record()
        return target

    def add_files(self):
        log.info("Copying selected file(s) to wheel")
        prefixes = self.path_prefixes_to_strip
        for i, (abs_path, rel_path) in enumerate(self.selected_files.files, 1):
            if not (i % 500):
                log.info(f"  {i} files added.")
            rel_path = strip_prefixes(rel_path, prefixes)
            self._add_file(abs_path, rel_path)

    def add_editable_pth_file(self):
        """
        Write a .pth path file in an editable wheel using configured editable_paths.
        """
        base_dir = self.base_dir.absolute()
        with self._write_to_zip(self.metadata.name + ".pth") as pth_file:
            log.debug(f"writing editable_path: {base_dir}")
            for rel_path in self.editable_paths:
                log.debug(f"writing editable_path: {base_dir / rel_path}")
                pth_file.write(str(base_dir / rel_path) + "\n")

    @property
    def dist_info_dir(self):
        return common.dist_info_name(self.metadata.name, self.metadata.version)

    def _add_file(self, abs_path, rel_path):
        # log.debug(f"Adding {abs_path!r} to zip file as {rel_path!r}")
        abs_path, rel_path = str(abs_path), str(rel_path)
        if os.sep != "/":
            # We always want to have /-separated paths in the zip file and in
            # RECORD
            rel_path = rel_path.replace(os.sep, "/")

        zinfo = ZipInfo.from_file(filename=abs_path, arcname=rel_path)
        # Set timestamps in zipfile for reproducible build
        zinfo.date_time = common.FLOT_ZIP_TIME

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
        date_time = common.FLOT_ZIP_TIME
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
        existing_metadata_files = {}
        for abs_meta, rel_meta in self.selected_metadata_files.files:
            # metadata files go directly in the dist_info directory, not in subdirs
            # no dupes allowed and some files also not allowed
            if rel_meta.name in existing_metadata_files:
                raise Exception(
                    f"Duplicated metadata file: {rel_meta} "
                    f"already exists at: {existing_metadata_files[rel_meta.name ]}"
                )

            if rel_meta.name in WELL_KNOWN_WHEEL_METADATA_FILES:
                raise Exception(
                    f"Invalid metadata file: {rel_meta} "
                    "cannot use a well known metadata file name."
                )

            self._add_file(abs_meta, f"{self.dist_info_dir}/{rel_meta.name}")

    def write_record(self):
        log.info("Writing the record of files")
        # Write a record of the files in the wheel
        with self._write_to_zip(self.dist_info_dir + "/RECORD") as f:
            for path, hsh, size in self.records:
                f.write("{},sha256={},{}\n".format(path, hsh, size))
            # RECORD itself is recorded with no hash or size
            f.write(self.dist_info_dir + "/RECORD,,\n")


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


def strip_prefixes(rel_path, prefixes):
    """
    Return a ``rel_path`` relative path  string stripped from the first found
    prefix of a list of ``prefixes`` path strings where rel_path starts with
    this prefix.
    Return the path unchanged if it has is no matching prefix.

    For example::

    >>> strip_prefixes("src/foo.py", ["lib", "src"])
    'foo.py'
    >>> strip_prefixes("src/lib/foo.py", ["lib", "src"])
    'lib/foo.py'
    >>> strip_prefixes("src/lib/foo.py", ["lib"])
    'src/lib/foo.py'
    >>> strip_prefixes("foo.py", ["lib"])
    'foo.py'
    >>> strip_prefixes("foo.py", [])
    'foo.py'
    """
    rel_path = str(rel_path)
    for prefix in prefixes:
        if rel_path.startswith(prefix):
            return rel_path.replace(prefix, "", 1).lstrip("/")
    return rel_path

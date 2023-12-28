#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import io
import logging
import tarfile
from copy import copy
from gzip import GzipFile
from pathlib import Path
from posixpath import join as pjoin

from . import common

log = logging.getLogger(__name__)


def make_sdist(
    pyproject_file=None,
    output_dir=None,
):
    """
    Make an sdist, return the built archive path.
    """
    builder = SdistBuilder.from_pyproject_file(
        pyproject_file=pyproject_file,
    )
    sdist = builder.build(output_dir=output_dir)
    log.info(f"Built sdist: {sdist}")
    return sdist


class SdistBuilder:
    def __init__(
        self,
        pyproject_file,
        metadata,
        entrypoints,
        includes=(),
        excludes=(),
        metadata_files=(),
        sdist_scripts=(),
        wheel_scripts=(),
        sdist_extra_includes=(),
        sdist_extra_excludes=(),
    ):
        log.debug(f"SdistBuilder: {pyproject_file}")
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

        self.selected_extra_files = common.FileSelector(
            base_dir=self.base_dir,
            includes=sdist_extra_includes,
            excludes=sdist_extra_excludes,
            label="sdist extra",
        )

        self.sdist_scripts = common.FileSelector(
            includes=sdist_scripts,
            base_dir=self.base_dir,
            label="sdist scripts",
        )

        self.wheel_scripts = common.FileSelector(
            includes=wheel_scripts,
            base_dir=self.base_dir,
            label="wheel scripts",
        )

    @classmethod
    def from_pyproject_file(
        cls,
        pyproject_file=None,
    ):
        """
        Create an sdisin target_dir, default: <pyproject file parent>/dist
        from an arbitrary pyproject.toml file path, default: "pyproject.toml".
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
            sdist_extra_includes=project_info.sdist_extra_includes,
            sdist_extra_excludes=project_info.sdist_extra_excludes,
            sdist_scripts=project_info.sdist_scripts,
            wheel_scripts=project_info.wheel_scripts,
        )

    @property
    def sdist_filename(self):
        return f"{self.dist_name}.tar.gz"

    @property
    def dist_name(self):
        return common.normalize_dist_name(self.metadata.name, self.metadata.version)

    def build(self, output_dir=None):
        """
        Build sdist and return sdist file path.
        """
        common.run_scripts(self.pyproject_file, self.sdist_scripts.files)

        output_dir = (
            output_dir and Path(output_dir).absolute() or Path(self.pyproject_file.parent) / "dist"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / self.sdist_filename

        mtime = common.FLOT_EPOCH_TIMESTAMP
        with GzipFile(str(target), mode="wb", mtime=mtime) as gz:
            with tarfile.TarFile(
                str(target),
                mode="w",
                fileobj=gz,
                format=tarfile.PAX_FORMAT,
            ) as tar_file:
                self.add_files(tar_file, mtime)
                self.write_metadata(tar_file, mtime)

        return target

    def add_files(self, tar_file, mtime):
        log.info("Copying selected file(s) to sdist")
        seen_paths = set()
        for i, (abs_path, rel_path) in enumerate(self._select_all_files(), 1):
            if rel_path in seen_paths:
                continue
            self._add_file(
                abs_path=abs_path,
                tar_file=tar_file,
                mtime=mtime,
                rel_path=rel_path,
            )
            seen_paths.add(rel_path)
            if not (i % 500):
                log.info(f"  {i} files added.")

    def _select_all_files(self):
        yield from self.selected_files.files
        yield from self.selected_extra_files.files
        yield from self.selected_metadata_files.files
        yield from self.sdist_scripts.files
        yield from self.wheel_scripts.files
        # Always include the pyproject file at the root renaming to use the
        # standard name
        ppt_abs_path = self.pyproject_file.absolute()
        ppt_rel_path = Path("pyproject.toml")
        yield ppt_abs_path, ppt_rel_path

    def _add_file(self, abs_path, tar_file, mtime, rel_path=None):
        if not rel_path:
            # If not provided, create the rel_path as relative to the pyproject
            # dir otherwise the includes/excludes will no longer work if trying
            # to build a wheel from an sdist
            rel_path = Path(abs_path).relative_to(self.pyproject_dir)

        # log.debug(f"Adding {abs_path!r} to tar file as {rel_path!r}")
        abs_path, rel_path = str(abs_path), str(rel_path)
        ti = tar_file.gettarinfo(abs_path, arcname=pjoin(self.dist_name, rel_path))
        ti = clean_tarinfo(ti, mtime)

        if ti.isreg():
            with open(abs_path, "rb") as f:
                tar_file.addfile(ti, f)
        else:
            tar_file.addfile(ti)  # Symlinks & ?

    def write_metadata(self, tar_file, mtime):
        log.info("Writing PKG-INFO metadata file")

        stream = io.StringIO()
        self.metadata.write_metadata_file(stream)
        pkg_info = stream.getvalue().encode()
        ti = tarfile.TarInfo(pjoin(self.dist_name, "PKG-INFO"))
        ti.size = len(pkg_info)
        ti = clean_tarinfo(ti, mtime)
        tar_file.addfile(ti, io.BytesIO(pkg_info))


def clean_tarinfo(ti, mtime=None):
    """Clean metadata from a TarInfo object to make it more reproducible.

    - Set uid & gid to 0
    - Set uname and gname to ""
    - Normalise permissions to 644 or 755
    - Set mtime if not None
    """
    ti = copy(ti)
    ti.uid = 0
    ti.gid = 0
    ti.uname = ""
    ti.gname = ""
    ti.mode = common.normalize_file_permissions(ti.mode)
    if mtime is not None:
        ti.mtime = mtime
    return ti

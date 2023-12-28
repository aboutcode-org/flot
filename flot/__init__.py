#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import argparse
import logging
import os
import pathlib
import tarfile
from contextlib import contextmanager
from pathlib import Path
from shutil import unpack_archive
from tempfile import TemporaryDirectory

description = """Flot is a tool to easily build multiple packages (wheel
and sdist) from a single repo without having to create a subdir or another repo
for each package.
"""

__version__ = "0.7.2"


log = logging.getLogger(__name__)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.description = description
    here = Path.cwd()
    parser.add_argument(
        "--pyproject",
        type=Path,
        nargs="?",
        default=here / "pyproject.toml",
        help="pyproject.toml file path. Default: <current directory>/pyproject.toml",
    )

    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=here / "dist",
        type=Path,
        nargs="?",
        help=(
            "Output directory where to create the wheel and sdist. "
            "Will be created if it does not exists. "
            "Default: <current directory>/dist/"
        ),
    )

    parser.add_argument(
        "--wheel",
        action="store_true",
        help=(
            "Build a wheel. Default if no option selected. "
            "If both --wheel and --sdist are specified, the sdist is built "
            "first, then the wheel is built from the extracted sdist to "
            "ensure that the wheel and sdist match."
        ),
    )

    parser.add_argument(
        "--sdist",
        action="store_true",
        help="Build an sdist.",
    )

    parser.add_argument(
        "--wheel-tag",
        dest="wheel_tag",
        default="py3-none-any",
        type=str,
        nargs="?",
        help="Optional wheel tag. Has no effect on sdist. Default: py3-none-any",
    )

    parser.add_argument("-v", "--version", action="version", version=f"flot {__version__}")

    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)

    enable_logging(level=logging.DEBUG if args.debug else logging.INFO)

    log.debug("Parsed arguments %r", args)

    build_wheel = args.wheel
    build_sdist = args.sdist

    print("Building from pyproject:", args.pyproject)
    print("output in :", args.output_dir)

    from . import sdist
    from . import wheel

    if not (build_wheel or build_sdist):
        build_wheel = True

    if build_sdist:
        sdn = sdist.make_sdist(
            pyproject_file=args.pyproject,
            output_dir=args.output_dir,
        )
        if build_wheel:
            with unpacked_tarball(sdn) as tmpdir:
                sdist_dir = Path(tmpdir)
                wheel.make_wheel(
                    pyproject_file=sdist_dir / "pyproject.toml",
                    output_dir=args.output_dir,
                    wheel_tag=args.wheel_tag,
                )
                print("using wheel tag:", args.wheel_tag)
                print("from unpacked sdist:", tmpdir)

    else:
        wheel.make_wheel(
            pyproject_file=args.pyproject,
            output_dir=args.output_dir,
            wheel_tag=args.wheel_tag,
        )
        print("using wheel tag:", args.wheel_tag)


def enable_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


@contextmanager
def unpacked_tarball(path):
    tf = tarfile.open(str(path))
    with TemporaryDirectory() as tmpdir:
        tf.extractall(tmpdir)
        files = os.listdir(tmpdir)
        assert len(files) == 1, files
        yield os.path.join(tmpdir, files[0])

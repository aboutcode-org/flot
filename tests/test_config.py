#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import logging
from pathlib import Path

import pytest

from flot import config

data_dir = Path(__file__).parent / "data"


def test_load_basic():
    project_info = config.read_pyproject_file(data_dir / "basic" / "my-pyproject.toml")
    expected = {
        "entrypoints": {},
        "excludes": ["**/.git/*", "**/.hg/*"],
        "includes": ["**/*"],
        "metadata": {
            "name": "package1",
            "requires_dist": [],
            "version": "1.0.0",
            "summary": "foo",
        },
        "metadata_files": [],
        "referenced_files": [],
        "reqs_by_extra": {},
        "sdist_extra_excludes": ["**/.git/*", "**/.hg/*"],
        "sdist_extra_includes": [],
        "editable_paths": [],
        "wheel_path_prefixes_to_strip": [],
        "sdist_scripts": [],
        "wheel_scripts": [],
    }
    assert project_info.to_dict() == expected


def test_toml_with_entry_points():
    project_info = config.read_pyproject_file(data_dir / "entrypoints_valid" / "pyproject.toml")
    expected = {
        "editable_paths": [],
        "entrypoints": {
            "console_scripts": {"pkg_script": "package1:main"},
            "myplugins": {"package1": "package1:main"},
        },
        "excludes": ["**/.git/*", "**/.hg/*"],
        "includes": ["module1.py"],
        "metadata": {
            "name": "package1",
            "requires_dist": [],
            "summary": "module1 desc",
            "version": "1.0",
        },
        "metadata_files": [],
        "referenced_files": [],
        "reqs_by_extra": {},
        "sdist_extra_excludes": ["**/.git/*", "**/.hg/*"],
        "sdist_extra_includes": [],
        "wheel_path_prefixes_to_strip": [],
        "sdist_scripts": [],
        "wheel_scripts": [],
    }
    assert project_info.to_dict() == expected


def test_load_normalization():
    proj = config.read_pyproject_file(data_dir / "normalization" / "pyproject.toml")
    assert proj.metadata["name"] == "my-python-module"


def test_load_pep621():
    proj = config.read_pyproject_file(data_dir / "pep621" / "pyproject.toml")
    assert proj.metadata["name"] == "module1"
    assert proj.metadata["version"] == "1.0.0"
    assert proj.metadata["description_content_type"] == "text/x-rst"
    # Remove all whitespace from requirements so we don't check exact format:
    assert {r.replace(" ", "") for r in proj.metadata["requires_dist"]} == {
        "docutils",
        "requests>=2.18",
        'pytest;extra=="test"',  # from [project.optional-dependencies]
        "mock;extra==\"test\"and(python_version<'3.6')",
    }
    assert proj.metadata["author_email"] == "Sir Röbin <robin@camelot.uk>"
    assert proj.entrypoints["flit_test_example"]["foo"] == "module1:main"


def test_load_pep621_nodynamic():
    proj = config.read_pyproject_file(data_dir / "pep621_nodynamic" / "pyproject.toml")
    assert proj.metadata["name"] == "module1"
    assert proj.metadata["version"] == "0.3"
    assert proj.metadata["summary"] == "Statically specified description"


def test_misspelled_key():
    with pytest.raises(config.ConfigError) as e_project_info:
        config.read_pyproject_file(data_dir / "misspelled-key.toml")

    assert "Description file" in str(e_project_info.value)


def test_description_file():
    project_info = config.read_pyproject_file(data_dir / "description-file" / "package1.toml")
    assert project_info.metadata["summary"] == "short description"
    assert project_info.metadata["description"] == "Sample description for test.\n"
    assert project_info.metadata["description_content_type"] == "text/x-rst"


def test_missing_description_file():
    with pytest.raises(config.ConfigError, match=r"Description file .* does not exist"):
        config.read_pyproject_file(data_dir / "description-missing" / "package1.toml")


def test_bad_description_extension(caplog):
    project_info = config.read_pyproject_file(
        data_dir / "description-bad" / "bad-description-ext.toml"
    )
    assert project_info.metadata["description_content_type"] is None
    assert any((r.levelno == logging.WARN and "Unknown extension" in r.msg) for r in caplog.records)


def test_with_wheel_path_prefixes_to_strip():
    project_info = config.read_pyproject_file(data_dir / "advanced_toml" / "pyproject.toml")
    expected = {
        "entrypoints": {},
        "excludes": ["**/.git/*", "**/.hg/*"],
        "includes": ["src/module3.py"],
        "metadata": {
            "name": "module3",
            "requires_dist": [],
            "summary": "module3 desc",
            "version": "1.0",
        },
        "metadata_files": ["LICENSE"],
        "referenced_files": [],
        "reqs_by_extra": {},
        "sdist_extra_excludes": ["**/.git/*", "**/.hg/*"],
        "sdist_extra_includes": ["foo.txt"],
        "editable_paths": ["src"],
        "wheel_path_prefixes_to_strip": ["src"],
        "sdist_scripts": [],
        "wheel_scripts": [],
    }
    assert project_info.to_dict() == expected


path_include_tests = [
    ("../bar", "contains relative .."),
    ("foo/../../bar", "contains relative .."),
    ("/home", "absolute path"),
    ("foo:bar", "bad character"),
]


@pytest.mark.parametrize(("path", "err_match"), path_include_tests)
def test_bad_includes_paths(path, err_match):
    toml_cfg = {
        "project": {
            "name": "foo",
            "version": "1.0.0",
            "description": "desc",
        },
        "tool": {"flot": {"includes": [path]}},
    }
    with pytest.raises(config.ConfigError, match=err_match):
        config.prep_pyproject_config(toml_cfg, None)


@pytest.mark.parametrize(("path", "err_match"), path_include_tests)
def test_bad_sdist_extra_includes_paths(path, err_match):
    toml_cfg = {
        "project": {
            "name": "foo",
            "version": "1.0.0",
            "description": "desc",
        },
        "tool": {"flot": {"includes": ["foo"], "sdist_extra_includes": [path]}},
    }

    with pytest.raises(config.ConfigError, match=err_match):
        config.prep_pyproject_config(toml_cfg, None)


@pytest.mark.parametrize(("path", "err_match"), path_include_tests)
def test_bad_metadata_files_paths(path, err_match):
    toml_cfg = {
        "project": {
            "name": "foo",
            "version": "1.0.0",
            "description": "desc",
        },
        "tool": {"flot": {"includes": ["foo"], "metadata_files": [path]}},
    }

    with pytest.raises(config.ConfigError, match=err_match):
        config.prep_pyproject_config(toml_cfg, None)


@pytest.mark.parametrize(
    ("proj_bad", "err_match"),
    [
        ({"version": 1}, r"\bstr\b"),
        ({"license": {"fromage": 2}}, "[Uu]nrecognised"),
        ({"license": {"file": "LICENSE", "text": "xyz"}}, "both"),
        ({"license": {}}, "required"),
        ({"keywords": "foo"}, "list"),
        ({"keywords": ["foo", 7]}, "strings"),
        ({"entry-points": {"foo": "module1:main"}}, "entry-point.*tables"),
        ({"entry-points": {"group": {"foo": 7}}}, "entry-point.*string"),
        (
            {"entry-points": {"gui_scripts": {"foo": "a:b"}}},
            r"\[project\.gui-scripts\]",
        ),
        ({"scripts": {"foo": 7}}, "scripts.*string"),
        ({"gui-scripts": {"foo": 7}}, "gui-scripts.*string"),
        ({"optional-dependencies": {"test": "requests"}}, "list.*optional-dep"),
        ({"optional-dependencies": {"test": [7]}}, "string.*optional-dep"),
        ({"dynamic": ["classifiers"]}, "does not support dynamic"),
        ({"dynamic": ["version"]}, "does not support dynamic"),
        ({"authors": ["thomas"]}, r"author.*\bdict"),
        ({"maintainers": [{"title": "Dr"}]}, r"maintainer.*title"),
    ],
)
def test_bad_pep621_project_info(proj_bad, err_match):
    proj = {"name": "module1", "version": "1.0", "description": "x"}
    proj.update(proj_bad)
    with pytest.raises(config.ConfigError, match=err_match):
        config.read_pep621_metadata(proj, data_dir / "pep621")


@pytest.mark.parametrize(
    ("readme", "err_match"),
    [
        ({"file": "README.rst"}, "required"),
        ({"file": "README.rst", "content-type": "text/x-python"}, "content-type"),
        ("/opt/README.rst", "relative"),
        ({"file": "README.rst", "text": "", "content-type": "text/x-rst"}, "both"),
        ({"content-type": "text/x-rst"}, "required"),
        (
            {"file": "README.rst", "content-type": "text/x-rst", "a": "b"},
            "[Uu]nrecognised",
        ),
        (5, r"readme.*string"),
    ],
)
def test_bad_pep621_readme(readme, err_match):
    proj = {"name": "module1", "version": "1.0", "description": "x", "readme": readme}
    with pytest.raises(config.ConfigError, match=err_match):
        config.read_pep621_metadata(proj, data_dir / "pep621")

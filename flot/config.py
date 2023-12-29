#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# Copyright (c) 2015, Thomas Kluyver and contributors
# Based on https://github.com/pypa/flit/ and heavily modified

import errno
import logging
import os.path as osp
import re
from email.headerregistry import Address
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .versionno import normalize_version

log = logging.getLogger(__name__)


class ConfigError(ValueError):
    pass


pep621_allowed_fields = {
    "name",
    "version",
    "description",
    "readme",
    "requires-python",
    "license",
    "authors",
    "maintainers",
    "keywords",
    "classifiers",
    "urls",
    "scripts",
    "gui-scripts",
    "entry-points",
    "dependencies",
    "optional-dependencies",
}


def read_pyproject_file(pyproject_file=None):
    """
    Read and check the "pyproject.toml-like" pyproject_file project file.
    """
    pyproject_file = pyproject_file or "pyproject.toml"
    pyproject_file = Path(pyproject_file).absolute()
    pyproject = tomllib.loads(pyproject_file.read_text("utf-8"))
    return prep_pyproject_config(pyproject, pyproject_file)


def prep_pyproject_config(pyproject_data, path):
    """
    Return a ProjectInfo loaded from pyproject.toml and prepare common metadata
    """
    if "project" not in pyproject_data:
        raise ConfigError(f"[project] not found in {path}")

    project_info = read_pep621_metadata(pyproject_data["project"], path)

    flot = pyproject_data.get("tool", {}).get("flot", {})
    if not flot:
        raise ConfigError(f"[tool.flot] not found in {path}")

    flot_config = _get_flot_config(flot)
    for name, value in flot_config.items():
        if value:
            setattr(project_info, name, value)

    return project_info


def _get_flot_config(flot_config):
    """
    Return a mapping of config data found in a pyproject.toml [tool.flot] section.
    """
    known_flot_keys = {
        "includes",
        "excludes",
        "metadata_files",
        "wheel_path_prefixes_to_strip",
        "editable_paths",
        "sdist_extra_includes",
        "sdist_extra_excludes",
        "sdist_scripts",
        "wheel_scripts",
    }
    unknown_keys = set(flot_config) - known_flot_keys
    if unknown_keys:
        raise ConfigError(f"Unknown keys in [tool.flot]: " + ", ".join(unknown_keys))

    includes = flot_config.get("includes", [])
    if not includes:
        raise ConfigError("includes should contain at least one file or directory")
    includes = _check_glob_patterns(includes, "includes")

    base_excludes = ["**/.git/*", "**/.hg/*"]

    excludes = base_excludes + flot_config.get("excludes", [])
    excludes = _check_glob_patterns(excludes, "excludes")

    metadata_files = flot_config.get("metadata_files", [])
    metadata_files = _check_glob_patterns(metadata_files, "metadata_files")

    wheel_path_prefixes_to_strip = flot_config.get("wheel_path_prefixes_to_strip", [])
    if wheel_path_prefixes_to_strip:
        _check_list_of_str(flot_config, "wheel_path_prefixes_to_strip")

    editable_paths = flot_config.get("editable_paths", [])
    if editable_paths:
        _check_list_of_str(flot_config, "editable_paths")

    sdist_extra_includes = flot_config.get("sdist_extra_includes", [])
    sdist_extra_includes = _check_glob_patterns(sdist_extra_includes, "sdist_extra_includes")

    sdist_extra_excludes = base_excludes + flot_config.get("sdist_extra_excludes", [])
    sdist_extra_excludes = _check_glob_patterns(sdist_extra_excludes, "sdist_extra_excludes")

    sdist_scripts = flot_config.get("sdist_scripts", [])
    if sdist_scripts:
        _check_list_of_str(flot_config, "sdist_scripts")

    wheel_scripts = flot_config.get("wheel_scripts", [])
    if wheel_scripts:
        _check_list_of_str(flot_config, "wheel_scripts")

    return dict(
        includes=includes,
        excludes=excludes,
        metadata_files=metadata_files,
        wheel_path_prefixes_to_strip=wheel_path_prefixes_to_strip,
        editable_paths=editable_paths,
        sdist_extra_includes=sdist_extra_includes,
        sdist_extra_excludes=sdist_extra_excludes,
        sdist_scripts=sdist_scripts,
        wheel_scripts=wheel_scripts,
    )


def _check_glob_patterns(pats, clude):
    """Check and normalise a list of glob patterns (like for includes or excludes)"""
    if not isinstance(pats, list):
        raise ConfigError(f"{clude} patterns must be a list")

    # Windows filenames can't contain these (nor * or ?, but they are part of
    # glob patterns) - https://stackoverflow.com/a/31976060/434217
    bad_chars = re.compile(r'[\000-\037<>:"\\]')

    normed = []

    for p in pats:
        if bad_chars.search(p):
            raise ConfigError(
                '{} pattern {!r} contains bad characters (<>:"\\ or control characters)'.format(
                    clude, p
                )
            )

        normp = osp.normpath(p)

        if osp.isabs(normp):
            raise ConfigError("{} pattern {!r} is an absolute path".format(clude, p))
        if ".." in normp:
            raise ConfigError(
                f"{clude} pattern {p!r} contains relative .. "
                "and may point out of the base directory"
            )
        normed.append(normp)

    return normed


class ProjectInfo:
    def __init__(self):
        self.metadata = {}
        self.reqs_by_extra = {}
        self.entrypoints = {}
        self.referenced_files = []
        self.includes = []
        self.excludes = []
        self.metadata_files = []
        self.wheel_path_prefixes_to_strip = []
        self.editable_paths = []
        self.sdist_extra_includes = []
        self.sdist_extra_excludes = []
        self.sdist_scripts = []
        self.wheel_scripts = []

    def add_scripts(self, scripts_dict):
        if scripts_dict:
            self.entrypoints["console_scripts"] = scripts_dict

    def to_dict(self):
        return dict(
            metadata=self.metadata,
            reqs_by_extra=self.reqs_by_extra,
            entrypoints=self.entrypoints,
            referenced_files=self.referenced_files,
            includes=self.includes,
            excludes=self.excludes,
            metadata_files=self.metadata_files,
            wheel_path_prefixes_to_strip=self.wheel_path_prefixes_to_strip,
            editable_paths=self.editable_paths,
            sdist_extra_includes=self.sdist_extra_includes,
            sdist_extra_excludes=self.sdist_extra_excludes,
            sdist_scripts=self.sdist_scripts,
            wheel_scripts=self.wheel_scripts,
        )


readme_ext_to_content_type = {
    ".rst": "text/x-rst",
    ".md": "text/markdown",
    ".txt": "text/plain",
}


def description_from_file(rel_path: str, proj_dir: Path, guess_mimetype=True):
    if osp.isabs(rel_path):
        raise ConfigError("Readme path must be relative")

    desc_path = proj_dir / rel_path
    try:
        with desc_path.open("r", encoding="utf-8") as f:
            raw_desc = f.read()
    except IOError as e:
        if e.errno == errno.ENOENT:
            raise ConfigError("Description file {} does not exist".format(desc_path))
        raise

    if guess_mimetype:
        ext = desc_path.suffix.lower()
        try:
            mimetype = readme_ext_to_content_type[ext]
        except KeyError:
            log.warning("Unknown extension %r for description file.", ext)
            log.warning("  Recognised extensions: %s", " ".join(readme_ext_to_content_type))
            mimetype = None
    else:
        mimetype = None

    return raw_desc, mimetype


def _expand_requires_extra(re):
    for extra, reqs in sorted(re.items()):
        for req in reqs:
            if ";" in req:
                name, envmark = req.split(";", 1)
                yield '{} ; extra == "{}" and ({})'.format(name, extra, envmark)
            else:
                yield '{} ; extra == "{}"'.format(req, extra)


def _check_type(d, field_name, cls):
    if not isinstance(d[field_name], cls):
        raise ConfigError(
            "{} field should be {}, not {}".format(field_name, cls, type(d[field_name]))
        )


def _check_list_of_str(d, field_name):
    if not isinstance(d[field_name], list) or not all(isinstance(e, str) for e in d[field_name]):
        raise ConfigError("{} field should be a list of strings".format(field_name))


def read_pep621_metadata(proj, path) -> ProjectInfo:
    lc = ProjectInfo()
    metadata = lc.metadata

    if "name" not in proj:
        raise ConfigError("name must be specified under [project]")
    _check_type(proj, "name", str)
    metadata["name"] = proj["name"]

    unexpected_keys = proj.keys() - pep621_allowed_fields
    if unexpected_keys:
        log.warning(f"Unexpected keys under [project]: {', '.join(unexpected_keys)}")

    if "version" not in proj:
        raise ConfigError("version must be specified under [project]")
    _check_type(proj, "version", str)
    metadata["version"] = normalize_version(proj["version"])

    if "description" not in proj:
        raise ConfigError("description must be specified under [project]")
    _check_type(proj, "description", str)
    metadata["summary"] = proj["description"]

    if "readme" in proj:
        readme = proj["readme"]
        if isinstance(readme, str):
            lc.referenced_files.append(readme)
            desc_content, mimetype = description_from_file(readme, path.parent)

        elif isinstance(readme, dict):
            unrec_keys = set(readme.keys()) - {"text", "file", "content-type"}
            if unrec_keys:
                raise ConfigError("Unrecognised keys in [project.readme]: {}".format(unrec_keys))
            if "content-type" in readme:
                mimetype = readme["content-type"]
                mtype_base = mimetype.split(";")[0].strip()  # e.g. text/x-rst
                if mtype_base not in readme_ext_to_content_type.values():
                    raise ConfigError("Unrecognised readme content-type: {!r}".format(mtype_base))
                # TODO: validate content-type parameters (charset, md variant)?
            else:
                raise ConfigError("content-type field required in [project.readme] table")
            if "file" in readme:
                if "text" in readme:
                    raise ConfigError("[project.readme] should specify file or text, not both")
                lc.referenced_files.append(readme["file"])
                desc_content, _ = description_from_file(
                    readme["file"], path.parent, guess_mimetype=False
                )
            elif "text" in readme:
                desc_content = readme["text"]
            else:
                raise ConfigError("file or text field required in [project.readme] table")
        else:
            raise ConfigError("project.readme should be a string or a table")

        metadata["description"] = desc_content
        metadata["description_content_type"] = mimetype

    if "requires-python" in proj:
        metadata["requires_python"] = proj["requires-python"]

    if "license" in proj:
        _check_type(proj, "license", dict)
        license_tbl = proj["license"]
        unrec_keys = set(license_tbl.keys()) - {"text", "file"}
        if unrec_keys:
            raise ConfigError("Unrecognised keys in [project.license]: {}".format(unrec_keys))

        # TODO: Do something with license info.
        # The 'License' field in packaging metadata is a brief description of
        # a license, not the full text or a file path. PEP 639 will improve on
        # how licenses are recorded.
        if "file" in license_tbl:
            if "text" in license_tbl:
                raise ConfigError("[project.license] should specify file or text, not both")
            lc.referenced_files.append(license_tbl["file"])
        elif "text" in license_tbl:
            pass
        else:
            raise ConfigError("file or text field required in [project.license] table")

    if "authors" in proj:
        _check_type(proj, "authors", list)
        metadata.update(pep621_people(proj["authors"]))

    if "maintainers" in proj:
        _check_type(proj, "maintainers", list)
        metadata.update(pep621_people(proj["maintainers"], group_name="maintainer"))

    if "keywords" in proj:
        _check_list_of_str(proj, "keywords")
        metadata["keywords"] = ",".join(proj["keywords"])

    if "classifiers" in proj:
        _check_list_of_str(proj, "classifiers")
        metadata["classifiers"] = proj["classifiers"]

    if "urls" in proj:
        _check_type(proj, "urls", dict)
        project_urls = metadata["project_urls"] = []
        for label, url in sorted(proj["urls"].items()):
            project_urls.append("{}, {}".format(label, url))

    if "entry-points" in proj:
        _check_type(proj, "entry-points", dict)
        for grp in proj["entry-points"].values():
            if not isinstance(grp, dict):
                raise ConfigError("projects.entry-points should only contain sub-tables")
            if not all(isinstance(k, str) for k in grp.values()):
                raise ConfigError("[projects.entry-points.*] tables should have string values")
        if set(proj["entry-points"].keys()) & {"console_scripts", "gui_scripts"}:
            raise ConfigError(
                "Scripts should be specified in [project.scripts] or "
                "[project.gui-scripts], not under [project.entry-points]"
            )
        lc.entrypoints = proj["entry-points"]

    if "scripts" in proj:
        _check_type(proj, "scripts", dict)
        if not all(isinstance(k, str) for k in proj["scripts"].values()):
            raise ConfigError("[project.scripts] table should have string values")
        lc.entrypoints["console_scripts"] = proj["scripts"]

    if "gui-scripts" in proj:
        _check_type(proj, "gui-scripts", dict)
        if not all(isinstance(k, str) for k in proj["gui-scripts"].values()):
            raise ConfigError("[project.gui-scripts] table should have string values")
        lc.entrypoints["gui_scripts"] = proj["gui-scripts"]

    if "dependencies" in proj:
        _check_list_of_str(proj, "dependencies")
        reqs_noextra = proj["dependencies"]
    else:
        reqs_noextra = []

    if "optional-dependencies" in proj:
        _check_type(proj, "optional-dependencies", dict)
        optdeps = proj["optional-dependencies"]
        if not all(isinstance(e, list) for e in optdeps.values()):
            raise ConfigError("Expected a dict of lists in optional-dependencies field")
        for e, reqs in optdeps.items():
            if not all(isinstance(a, str) for a in reqs):
                raise ConfigError(f"Expected a string list for optional-dependencies ({e})")

        lc.reqs_by_extra = optdeps.copy()
        metadata["provides_extra"] = sorted(lc.reqs_by_extra.keys())

    metadata["requires_dist"] = reqs_noextra + list(_expand_requires_extra(lc.reqs_by_extra))

    if "dynamic" in proj:
        raise ConfigError("flot does not support dynamic fields")

    return lc


def pep621_people(people, group_name="author") -> dict:
    """Convert authors/maintainers from PEP 621 to core metadata fields"""
    names, emails = [], []
    for person in people:
        if not isinstance(person, dict):
            raise ConfigError("{} info must be list of dicts".format(group_name))
        unrec_keys = set(person.keys()) - {"name", "email"}
        if unrec_keys:
            raise ConfigError("Unrecognised keys in {} info: {}".format(group_name, unrec_keys))
        if "email" in person:
            email = person["email"]
            if "name" in person:
                email = str(Address(person["name"], addr_spec=email))
            emails.append(email)
        elif "name" in person:
            names.append(person["name"])

    res = {}
    if names:
        res[group_name] = ", ".join(names)
    if emails:
        res[group_name + "_email"] = ", ".join(emails)
    return res

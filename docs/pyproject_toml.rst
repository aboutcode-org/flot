The pyproject.toml config file
==============================

This file lives next to the module or package. With flot, you can use any name
you like, and have several of these TOML files throughout your codebase.

The pyproject.toml file format is specified at
https://packaging.python.org/en/latest/specifications/pyproject-toml

Flot extends this file with a ``[tools.flot]`` table as supported by the spec.


Minimal example
----------------

This is a minimum pyproject.toml example::

.. code-block:: toml

    [build-system]
    requires = ["flot"]
    build-backend = "flot.buildapi"

    [project]
    name = "astcheck"
    version = "1.0.0"
    description = "A frobinator to check ASTs"

    [tool.flot]
    includes = ["src"]


Beyond the ``[build-system]`` table, the few following fields are required:

- in the ``[project]`` table, the name, version and description fields.
- in the ``[tools.flot]`` table the ``includes`` field.



Build system section details
-----------------------------

This tells tools like pip to build your project with flot. It is a standard
defined by PEP 517. For a project using flot, pyproject.toml will start with this:

.. code-block:: toml

    [build-system]
    requires = ["flot"]
    build-backend = "flot.buildapi"


.. _pyproject_toml_project:


Project metadata  details
-----------------------------


To specify your project metadata, use the standard ``[project]`` TOML table,
as defined by :pep:`621` and now at
https://packaging.python.org/en/latest/specifications/pyproject-toml

The required ``[project]``fields name, version and description. The other
required field is ``includes`` in the ``[tools.flot]`` table.

A simple ``[project]`` table might look like this:

.. code-block:: toml

    [project]
    name = "astcheck"
    version = "1.0.0"
    description = "A frobinator to check ASTs"
    authors = [
        {name = "Thomas Kluyver", email = "thomas@kluyver.me.uk"},
    ]
    readme = "README.rst"
    classifiers = [
        "License :: OSI Approved :: MIT License",
    ]
    requires-python = ">=3.8"

The allowed fields are:

name
  The name your package will have on PyPI. This field is required.

version
  Version number as a string. This field is required.

description
  A one-line description of your project. This field is required.

readme
  A path (relative to the .toml file) to a file containing a longer description
  of your package to show on PyPI. This should be written in `reStructuredText
  <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_, Markdown or
  plain text, and the filename should have the appropriate extension
  (``.rst``, ``.md`` or ``.txt``). Alternatively, ``readme`` can be a table with
  either a ``file`` key (a relative path) or a ``text`` key (literal text), and
  an optional ``content-type`` key (e.g. ``text/x-rst``).

requires-python
  A version specifier for the versions of Python this requires, e.g. ``>=3.8,<4``.

license
  A table with either a ``file`` key (a relative path to a license file) or a
  ``text`` key (the license text). When using the ``text`` key, the common
  practice is to use an SPDX license expression.

authors
  A list of tables with ``name`` and ``email`` keys (both optional) describing
  the authors of the project.

maintainers
  Same format as authors.

keywords
  A list of words to help with searching for your package.

classifiers
  A list of `Trove classifiers <https://pypi.python.org/pypi?%3Aaction=list_classifiers>`_.
  Add ``Private :: Do Not Upload`` into the list to prevent a private package
  from being uploaded to PyPI by accident.

dependencies & optional-dependencies
  See :ref:`pyproject_project_dependencies`.

urls
  See :ref:`pyproject_project_urls`.

scripts & gui-scripts
  See :ref:`pyproject_project_scripts`.

entry-points
  See :ref:`pyproject_project_entrypoints`.

See https://packaging.python.org/en/latest/specifications/pyproject-toml for
extra details.

.. _pyproject_tools_flot_includes_excludes:


Flot table
--------------------

These fields are allowed in the ``[tools.flot]`` table

**includes (required)
excludes**

  List of paths or glob patterns for files to include or exclude in the wheel and sdist.
  These patterns are standard Python pathlib Path glob patterns evaluated relative
  to the directory of the pyproject.toml file. A file is included if its path
  matches any includes and does not match any excludes.
  See the glob documentation for details:
  https://docs.python.org/3/library/pathlib.html?highlight=pathlib glob#pathlib.Path.glob

Note that the following files are always ignored:

- Bytecode (``.pyc`` files and ``__pycache__`` directories) is excluded by
  default and cannot be included.
- Version control directories for git and mercurail: ``.git`` and ``.hg`` directory
  trees.


**sdist_extra_includes
sdist_extra_excludes**

  List of extra paths or glob patterns for files to include or exclude in the sdist.
  These are sdist additions to the includes/excludes and are evaluated separately.
  The definition is the same as for includes/excludes.


**wheel_path_prefixes_to_strip**

  List of path prefixes to strip from a file added in a wheel. When copying
  files selected using includes/excludes, the first matching prefix will be
  stripped from any path that starts with it.
  The typical usage is to strip the leading ``src/`` path
  segment when using a ``src/`` directory layout for your project.

**editable_paths**

  List of paths relative to the directory of the pyproject.toml file to include
  as "editable" paths (listed in the .pth file) in an editable installation.
  These paths will be added to the sys.path by an installer such as pip when
  running a ``pip install --editable`` command for a package built with flot
  either from a source checkout, a source archive or an sdist.
  Defaults to the directory of the pyproject.toml file if not provided.

**metadata_files**

  List of paths or glob patterns for metadata files to include in the wheel under the
  wheel dist-info directory. These are relative to the directory of pyproject.toml.
  The definition is the same as for includes. There is no default.
  Files matching these patterms are copied as-is in the root of the dist-info
  directory, ignoring any directory structure.

  This is an error if any file name is not unique or is the same as any standard
  wheel dist-info metadata file names:

- direct_url.json
- entry_points.txt
- INSTALLER
- METADATA
- RECORD
- REQUESTED
- WHEEL


**wheel_scripts
sdist_scripts**

  List of script paths relative to the directory of the pyproject.toml file to
  run at the begining of the wheel or sdist build. These are simple Python
  scripts. Each script is called in turn in a subprocess passing an argument
  the asbsolute path to the pyproject.toml.
  By default, ``flot`` and its dependencies are available. Scripts may have
  requirements for extra Python package to use at build time.
  These should be added to the  ``[build-system]`` table ``requires`` section.


Flot ``includes`` and ``excludes`` section details
---------------------------------------------------

Flot prefers explicit over implicit declarations of which files to include in
your package: you must specify explicitly which files to include in a wheel
or sdist.

For this, you give lists of paths or glob patterns as ``includes`` and ``excludes``.

For example:

.. code-block:: toml

    [tool.flot]
    includes = ["src/"]
    excludes = ["src/foobar.py"]


See the glob documentation for details:
https://docs.python.org/3/library/pathlib.html?highlight=glob#pathlib.Path.glob

Paths and glob patterns in excludes and includes must meet these rules:

- Must be relative paths from the directory of your pyproject.toml file.
- Cannot go outside that directory (no ``../`` paths)
- Always use ``/`` as a separator (POSIX style).
- Cannot contain control characters or ``<>:"\\``
- Can refer to directories. But to include include or exclude everything
  under a directory tree, including subdirectories, use a recursive glob pattern (``**``)
- Should match the case of the files they refer to, as case-insensitive matching
  is platform dependent.

These included and excluded files are added to wheel and sdist archives.


.. _pyproject_tools_flot_metadata_files:


Flot metadata files includes section
---------------------------------------

This list of paths or glob patterns has the same specification as the
``includes``.

They are added to:

- the wheel dist-info/  directory directly using only their file name, and
  ignoring any directory structure.

- the sdist archive directory using their actual path, including any directory.


Other project metadata
----------------------------

These sections are standard, as specified in the pyproject.toml documentation.

.. _pyproject_project_dependencies:

Dependencies
~~~~~~~~~~~~

The ``dependencies`` field is a list of other packages from PyPI that this
package needs. Each package may be followed by a version specifier like
``>=4.1``, and/or an `environment marker`_
after a semicolon. For example:

  .. code-block:: toml

      dependencies = [
          "requests >=2.6",
          "configparser; python_version == '2.7'",
      ]

The ``[project.optional-dependencies]`` table contains lists of packages needed
for every optional feature. The requirements are specified in the same format as
for ``dependencies``. For example:

  .. code-block:: toml

      [project.optional-dependencies]
      test = [
          "pytest >=2.7.3",
          "pytest-cov",
      ]
      doc = ["sphinx"]

You can call these optional features anything you want, although ``test`` and
``doc`` are common ones. You specify them for installation in square brackets
after the package name or directory, e.g. ``pip install '.[test]'``.


.. _pyproject_project_urls:

URLs table
~~~~~~~~~~

Your project's page on `pypi.org <https://pypi.org/>`_ can show a number of
links. You can point people to documentation or a bug tracker, for example.

This section is called ``[project.urls]`` in the file. You can use
any names inside it. Here it is for flot:

.. code-block:: toml

  [project.urls]
  Documentation = "https://flot.pypa.io"
  Source = "https://github.com/nexB/flot"

.. _pyproject_project_scripts:

Scripts section
~~~~~~~~~~~~~~~

This section is called ``[project.scripts]`` in the file.
Each key and value describes a shell command to be installed along with
your package. These work like setuptools 'entry points'. Here's the section
for flot:

.. code-block:: toml

    [project.scripts]
    flot = "flot:main"


This will create a ``flot`` command, which will call the function ``main()``
imported from :mod:`flot`.

A similar table called ``[project.gui-scripts]`` defines commands which launch
a GUI. This only makes a difference on Windows, where GUI scripts are run
without a console.

.. _pyproject_project_entrypoints:

Entry points sections
~~~~~~~~~~~~~~~~~~~~~

You can declare `entry points <http://entrypoints.readthedocs.io/en/latest/>`_
using sections named :samp:`[project.entry-points.{groupname}]`. E.g. to
provide a pygments lexer from your package:

.. code-block:: toml

    [project.entry-points."pygments.lexers"]
    dogelang = "dogelang.lexer:DogeLexer"

In each ``package:name`` value, the part before the colon should be an
importable module name, and the latter part should be the name of an object
accessible within that module. The details of what object to expose depend on
the application you're extending.

If the group name contains a dot, it must be quoted (``"pygments.lexers"``
above). Script entry points are defined in :ref:`scripts tables
<pyproject_project_scripts>`, so you can't use the group names
``console_scripts`` or ``gui_scripts`` here.



.. _environment marker: https://www.python.org/dev/peps/pep-0508/#environment-markers

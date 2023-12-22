The pyproject.toml config file
==============================

This file lives next to the module or package. With flot, you can use any name
you like, and have several of these TOML files throughout your codebase.

The pyproject.toml file format is specified at
https://packaging.python.org/en/latest/specifications/pyproject-toml

Flot extends this file with a ``[tools.flot]`` table as supported by the spec.

Build system section
--------------------

This tells tools like pip to build your project with flot. It's a standard
defined by PEP 517. For any new project using flot, it will look like this:

.. code-block:: toml

    [build-system]
    requires = ["flot"]
    build-backend = "flot.buildapi"

.. _pyproject_toml_project:

Core metadata
----------------

The way to specify project metadata is in a standard ``[project]`` TOML table,
as defined by :pep:`621` and now at
https://packaging.python.org/en/latest/specifications/pyproject-toml


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
  A one-line description of your project.

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

Flot includes and excludes section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flot prefers explicit over implicit declarations of which files to include in
your package: you must specify explicitly which files to include in a wheel
or sdist.

For this, you give lists of paths or glob patterns as
``includes`` and ``excludes``. For example:

.. code-block:: toml

    [tool.flot]
    includes = ["src/"]
    excludes = ["src/foobar.py"]


The paths in excludes and includes have these specifications:

- Always use ``/`` as a separator (POSIX style)
- Must be relative paths from the base directory
  (defaulting to the directory containing ``pyproject.toml``).
- Cannot go outside that directory (no ``../`` paths)
- Cannot contain control characters or ``<>:"\\``
- Can refer to directories, in which case they include or exclude everything
  under the directory, including subdirectories
- Should match the case of the files they refer to, as case-insensitive matching
  is platform dependent.
- Can use recursive glob patterns (``**``).
- Exclusions have priority over inclusions.
- Bytecode (``.pyc`` files and ``__pycache__`` directories) is excluded by default and cannot be included.
- Other default excludes are for version control ``.git`` and ``.hg`` directories.

These included and excluded files are added to wheel and sdist archives.


.. _pyproject_tools_flot_sdist_extra_includes_excludes:

Sdist extra includes and excludes section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``sdist_extra_includes`` and ``sdist_extra_excludes`` are lists of paths or
glob patterns with the same specification as the ``includes`` and ``excludes``
above.

These extra included and excluded files are added only to the sdist archive.

.. _pyproject_tools_flot_metadata_files:


metadata files includes section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These is  lists of paths or glob patterns with the same specification as the
``includes`` above. They must be 

The default is this list of patterns if not provided::

    metadata_files = ["README*", "LICENSE*", "LICENCE*", "COPYING*",]

These files must be in the same directory as the pyproject.toml.
They are added to:

- the wheel dist-info/  archive directory directly, ignoring the directory structure.
- the sdist archive directory.

.. _pyproject_tools_flot_wheel_path_prefixes_to_strip:


wheel_path_suffixes_to_strip section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a list of path prefix strings that will be stripped from any selected file
path added to a wheel. The typical usage is to strip the leading ``src`` path
segment when using a ``src/`` directory layout.

editable_paths section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a list of paths that will be available in the Python path when the package
is installed as "editable" from its sdists or from a checkout.


 
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

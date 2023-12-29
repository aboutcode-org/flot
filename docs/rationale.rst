Why use flot?
=============

``flot`` makes it easy to build Python packages, and leaves everything else,
like installation, publishing, and other hard things to other tools.

Specifically, the simple things are pure Python packages assembled simply from
a bunch of file paths, with no extra build steps. The vast majority of packages
on PyPI are like this and flot makes it dead easy to build these packages.

What, specifically, does flot make easy?

- ``flot`` builds wheels and sdists, nothing else. No command bloat.

- ``flot`` uses only pyproject.toml. No legacy menagerie of many files like a
  setup.cfg, some ini file, setup.py, MANIFEST.in or other manifest file.

- There is only one way to do things with ``flot`` .

- With ``flot``, there is no magic in which files, packages or modules to include in
  your packages.

- ``flot`` can build easily many packages from one code tree. Just create as many
  pyproject TOML files as you have packages, name them the way you want and you
  can build all of these without fuss.


About files selection and other efforts
-------------------------------------------

There have been many other efforts to improve the user experience of Python
packaging, such as `flit <https://pypi.org/project/flit/>`_, but before ``flot``,
these tended to provide complex features with a lot of magic discovery of modules.

Existing tools are trying to be smart about which files to include in a package
using magic discovery and guesses; this is byzantine and hard to understand and
debug.

Flot explicit files inclusion is better than implicit inclusion. ``flot`` assumes
little to nothing about your code structure. Files are not ``automatically``
included or excluded. Just provide a list of paths or path patterns to
include/exclude in your package.


Other options
-------------

If your package needs an extra build step, like with native C/C++ code, you
can still use flot using the "sdist_scripts" and "wheel_scripts" lists of
arbitrary Python scripts. Or you should consider setuptools.

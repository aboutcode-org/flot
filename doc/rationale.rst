Why use flot?
=============

flot enable the simplest way to build a simple Pythom package, and leaves
everything else, like installation, publishing, and other hard things to other
tools.

Specifically, the easy things are pure Python packages assembled simply from
a bunch of file paths, with no extra build steps. The vast majority of packages
on PyPI are like this and flot makes it dead easy to build these packages.

What, specifically, does flot make easy?

- Build wheels and sdists, nothing else. No command bloat.

- Use only pyproject.toml. No legacy menagerie of setup.cfg, ini, setup.py or
  other manifest.file. There is only one way to do things with ``flot``.
  
- No magic in files, packages or modules selection. Existing tools are trying to
  be smart about which files to include in a package using magic discovery and
  guesses; this is byzantine and hard to understand.

- Explicit files inclusion is better than implicit. ``flot`` assumes little to
  nothing. Just provide a list of paths to include in your package. Files are
  not ``automatically`` included or excluded.

- Build easily many packages from one code tree. Just create as many
  pyproject TOML files as you have packages, name them the way you want and you
  can build all of these without fuss.

There have been many other efforts to improve the user experience of Python
packaging, such as `flit <https://pypi.org/project/flit/>`_, but before ``flot`,
these tended to provide complex features with a lot of magic discovery of modules.

Flot provides a simple :pep:`517` API and it's only dependency is a toml library.


Other options
-------------

If your package needs an extra build step, like with native C/C++ code, you won't
be able to use flot directly.


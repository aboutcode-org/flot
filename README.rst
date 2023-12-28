**flot** is an easy tool to build Python packages (wheel and sdist) with no
magic and guesswork. Flot can also create one or more Python packages
from a single code tree, just by listing which files you want to include.

Because "Explicit is better than implicit" and "Simple is better than complex"

``flot`` takes the magic and guesswork away of which files are included in a
Python package: you just specify a list of paths or glob patterns for the files
you want to include or exclude in your package. No more mystery! Include data
files, multiple modules or any files as easily as listing their paths.

With ``flot`` you can also have multiple ``pyproject.toml`` files to enjoy the
benefits of a simpler monolithic code repo and still be able to easily share
and package multiple Pypi packages and foster the reuse of subsets of your larger
project, without having some imposed directory structure.

Unlike ``flot``, other Python build tools assume that you can only build a
single Python package from a given directory or repository and use a lot of
magic to find which module or file to include in your package.

Also, while ``flot`` promotes declarative builds, it is also possible to run
arbitrary Python scripts when you need more power.

See also `Why use Flot? <https://github.com/nexB/flot/blob/main/docs/rationale.rst>`_

Flot is derived from and based on a modified Flit https://github.com/pypa/flit/
by Thomas Kluyver @takluyver

It was started following this discussion https://github.com/pypa/flit/discussions/669


Install
-------

::

    pip install flot


Usage
-----

Say you're writing a module ``foobar`` - either as a single file ``foobar.py``,
or as a directory - and you want to distribute it.

1. Create a ``pyproject.toml`` file. It will look something like this::

       [build-system]
       requires = ["flot"]
       build-backend = "flot.buildapi"

       [project]
       name = "foobar"
       version = "1.0.0"
       description = "foobar frobinator"

       [tool.flot]
       includes = ["foobar.py"]

   You can edit this file to add other metadata, like URL for example to set up
   command line scripts or add your dependencies. See the ``pyproject.toml``
   documentation at https://github.com/nexB/flot/blob/main/docs/pyproject_toml.rst

2. Run this command to build your wheel in the dist/ directory::

       flot

Once your package is published to PyPI (I use the standard ``twine`` tool for this),
people can install it using ``pip`` or any other Python packaging tool just like
any other package. 

3. Say you're writing a second module ``baz`` as a single file ``baz.py``.
   Just create a second file named for instance ``baz-pyproject.toml``.
   It will look something like this::

       [build-system]
       requires = ["flot"]
       build-backend = "flot.buildapi"

       [project]
       name = "baz"
       version = "1.0.0"
       description = "baz frobinator"

       [tool.flot]
       includes = ["baz.py"]

4. Run this command to build a second wheel in the dist/ directory::

       flot --pyproject baz-pyproject.toml


You now have a second wheel built from the same tree with different content.

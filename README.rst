**Flot** is a simple way to create one or more Python packages from a single
repository or code tree, just listing the files you want top include.

Because "Explicit is better than implicit" and "Simple is better than complex."

You can now have multiple pyproject.toml files and enjoy the benefits of a
simpler monolithic code layout and still be able to easily share and package
multiple Pypi packages to foster reuse of subsets of your larger project.

Other tools assume that you can only build a single Python package from a given
directory or repository and use a lot of magic to find which module or file to
include in your package.

``flot`` takes the magic away: you just specify a list of paths or path patterns
for the files you want to include in your package. No mystery! Include data files,
multiple modules or any files as easily as listing their paths.

See `Why use Flot? <https://flot.readthedocs.io/en/latest/rationale.html>`_ for
more details.


Install
-------

::

    $ pip install flot


Usage
-----

Say you're writing a module ``foobar`` — either as a single file ``foobar.py``,
or as a directory — and you want to distribute it.

1. Install flot if you don't already have it::

       pip install flot

2. Create a ``pyproject.toml`` file in the directory containing the module.
   It will look something like this::

       [build-system]
       requires = ["flot >=0.5,<1"]
       build-backend = "flot.buildapi"

       [project]
       name = "foobar"
       version = "1.0.0"
       description = "foobar frobinator"
       authors = [{name = "Sir Robin", email = "robin@camelot.uk"}]

       [project.urls]
       Home = "https://github.com/sirrobin/foobar"

       [tool.flot]
       includes = ["foobar.py"]


   You can edit this file to add other metadata, for example to set up
   command line scripts. See the
   `pyproject.toml page <https://flit.readthedocs.io/en/latest/pyproject_toml.html#scripts-section>`_
   of the documentation.

3. Run this command to build your wheel in the dist/ directory::

       flot

Once your package is published to PyPI (like with the ``twine`` tool), people
can install it using ``pip`` or any other Python packaging tool just like any
other package. 

4. Say you're writing a second module ``baz`` as a single file ``baz.py``.
   Just create a second file named for instance ``baz-pyproject.toml``.
   It will look something like this::

       [build-system]
       requires = ["flot >=0.5,<1"]
       build-backend = "flot.buildapi"

       [project]
       name = "baz"
       version = "1.0.0"
       description = "baz frobinator"
       authors = [{name = "Sir Robin", email = "robin@camelot.uk"}]

       [project.urls]
       Home = "https://github.com/sirrobin/foobar"

       [tool.flot]
       includes = ["baz.py"]

5. Run this command to build a second wheel in the dist/ directory::

       flot --pyproject baz-pyproject.toml


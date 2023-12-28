Developing Flot
===============

To get a development installation of Flot itself::

    git clone https://github.com/nexB/flot.git

Create and activate a virtualenv::

    cd flot
    python -m virtualenv venv
    source venv/bin/activate
        
Then install flot in "editable" mode::

    pip install --editable .[test,doc]


Testing
-------

To run the tests in your current environment, run pytest::

    pytest

To run the tests in separate environments for each supported and available
Python version, run tox::

    tox

`tox <https://tox.readthedocs.io/en/latest/>`_ has many options.

Documentation
--------------

To build the documentation, run::

    cd doc
    make html
    


Releasing
----------

The checklist for a release is:

- All tests pass.
- The version is bumped with ``bump-my-version bump patch`` (or minor or major).
- The doc/history.rst file is updated with an entrey for this version.
- Everything is committed.
- Create and push a tag for this version. For `0.7.0`, use a `v0.7.0` tag.
- Run ``flot --wheel --sdist`` to build.
- Run some smoke tests to validate that the wheel installs and runs OK in an isolated envt.
- Publish to Pypi with ``twine upload dist/*``

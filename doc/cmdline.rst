Flot command line interface
===========================

All operations use the ``flot`` command.

Common options
--------------

.. program:: flot

.. option:: --pyproject <path>

   Path to a pyproject file. The default is ``pyproject.toml``.

.. option:: --output-dir <path>

    Directory where to create the wheel and sdist.
    Will be created if it does not exists.
    Defaults to dist/ in the current directory.

.. option:: --wheel

    Build a wheel from the package. Default action if nothing is specified.

.. option:: --wheel-tag

    Optional wheel tag. Defaults to "py3-any-none". Has no effect on sdist.

.. option:: --sdist

    Build a sdist from the package.

.. option::  --version

   Show the version of Flit and exit.

.. option:: --help

   Show help on the command-line interface.

.. envvar:: SOURCE_DATE_EPOCH

   To make reproducible builds, set this to a timestamp as a number of seconds
   since the start of the year 1970 in UTC, and document the value you used.
   On Unix systems, you can get a value for the current time by running::

       date +%s


   .. seealso::

      `The SOURCE_DATE_EPOCH specification
      <https://reproducible-builds.org/specs/source-date-epoch/>`__


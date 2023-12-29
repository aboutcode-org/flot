Flot command line interface
===========================

All operations use the ``flot`` command. Without any option, running ``flot``
will build a wheel::

    usage: flot [-h] [--pyproject [PYPROJECT]] [--output-dir [OUTPUT_DIR]] [--wheel] [--sdist]
                [--wheel-tag [WHEEL_TAG]] [-v]

    Flot is a tool to easily build multiple packages (wheel and sdist) from a single repo without
    having to create a subdir or another repo for each package.

    optional arguments:
      -h, --help            show this help message and exit
      --pyproject [PYPROJECT]
                            pyproject.toml file path. Default: <current directory>/pyproject.toml
      --output-dir [OUTPUT_DIR]
                            Output directory where to create the wheel and sdist. Will be created if
                            it does not exists. Default: <current directory>/dist/
      --wheel               Build a wheel. Default if no option selected. If both --wheel and --sdist
                            are specified, the sdist is built first, then the wheel is built from the
                            extracted sdist to ensure that the wheel and sdist match.
      --sdist               Build an sdist.
      --wheel-tag [WHEEL_TAG]
                            Optional wheel tag. Has no effect on sdist. Default: py3-none-any
      -v, --version         show program's version number and exit


.. envvar:: SOURCE_DATE_EPOCH

   To make reproducible builds, set this to a timestamp as a number of seconds
   since the start of the year 1970 in UTC, and document the value you used.
   On Unix systems, you can get a value for the current time by running::

       date +%s

   .. seealso::

      `The SOURCE_DATE_EPOCH specification
      <https://reproducible-builds.org/specs/source-date-epoch/>`__


Reproducible builds
===================

Wheels and sdist built by flot are reproducible: if you build from the same
source code, you should be able to make wheels that are exactly identical,
byte for byte. This is useful for verifying software. For more details, see
`reproducible-builds.org <https://reproducible-builds.org/>`__.

To achieve this reproducibility, the dates, usernames and permissions are either
normalized or removed such that they do not change between two runs.


Normalising timestamps
~~~~~~~~~~~~~~~~~~~~~~

All files timestamps are fixed to this ISO UTC date: 2022-02-02T02:02:02

These timestamps can be overridden by the environment variable
:envvar:`SOURCE_DATE_EPOCH` using a Unix timestamp as specified for reproducible
builds at https://reproducible-builds.org/docs/source-date-epoch/

.. code-block:: shell

   SOURCE_DATE_EPOCH=$(date --iso-8601=seconds --utc)
   flot

For instance with 2023-03-23T23:23:23, the `SOURCE_DATE_EPOCH` value would be:

.. code-block:: python

    >>> from datetime import datetime
    >>> int(datetime.fromisoformat("2023-03-23T23:23:23").timestamp())
    1679610203

And you would use it this way:

.. code-block:: shell

   SOURCE_DATE_EPOCH=1679610203
   flot


Note that dates before 1980 may not work well with zip that does not support
dates before 1980-01-01T00:00:00. No check is done and this will likely fail
in arcane ways.


Normalising permission bits
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flot normalises the permission bits of files copied into a wheel to either
755 (executable) or 644. This means that a file is readable by all users
and writable only by the user who owns it.

The most popular version control systems only track the executable bit,
so checking out the same repository on systems with different umasks
(e.g. Debian and Fedora) produces files with different permissions.


Other sdist normalisation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For an sdist tarball, these normalisations are applied:

- Set uid & gid to 0
- Set uname and gname to ""
- Normalise permissions to 644 or 755 as explained above
- Set mtime to 2022-02-02T02:02:02


Other wheel normalisation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a wheel zip, these normalisations are applied:

- Normalize mode bits
- Set date_time to 2022-02-02T02:02:02

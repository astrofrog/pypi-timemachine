A PyPI time machine
-------------------

Do you wish you could just install packages with pip as if you were at
some fixed date in the past? If so, the PyPI time machine is for you!

**Disclaimer:** this is alpha-quality software - for now it is a quick hack,
but I'd love to make this more robust/usable with your help!

Installing
~~~~~~~~~~

To install::

   pip install pypi-timemachine

Using
~~~~~

Once installed, you can run a PyPI server with::

   pypi-timemachine 2021-02-03

or if you need to specify a precise time (in UTC)::

   pypi-timemachine 2021-02-03T12:33:02

This will start up a webapp running uvicorn, and will print out a line such as::

    pypi-timemachine server listening at http://localhost:5000  (Press CTRL+C to quit)
      Hint: Setting the environment variable PIP_INDEX_URL="http://localhost:5000" is one way to configure pip to use this timemachine

You can then configure pip to use the time machine, for example::

   pip install --index-url http://127.0.0.1:5000/ astropy

and this will then install the requested packages and all dependencies,
ignoring any releases after the cutoff date specified above.

For convenience, it is also possible to specify the cutoff date as part of the
repository URL, using the pattern `http://{host}/snapshot/{cutoff_date}/`.
Cutoff date can be either an RFC 3339 timestamp (e.g. `2006-12-02T02:07:43Z`)
or a simple date (e.g., 2006-12-02). For example::

   pip install --index-url http://127.0.0.1:5000/snapshot/2024-12-03 astropy

Would install the requested packages and all dependencies from the date given in
the index URL.

It is possible to run the time machine against a custom Python package
repository, provided it includes date metadata as defined in PEP-700,
specifically the `upload-time` field::

  pypi-timemachine 2021-02-03 --index-url https://my-custom-repo/simple/

How it works
~~~~~~~~~~~~

`pypi-timemachine` builds upon the `simple-repository`_ stack, and uses the
standards based PEP-503 repository definition to serve packages.
In order to filter by time, the upstream repository must provide PEP-700
metadata (which PyPI does).
The results are filtered by pypi-timemachine, and then served as HTML or JSON
via the standard PEP-503 interface.


Caveats/warnings
~~~~~~~~~~~~~~~~

If a package is already installed, pip will not try installing it again.
This means that if e.g. you try and run pip as described above, but the
package you are trying to install (or any of its dependencies) is
already installed, no matter how recent the version, it will not be
installed again. Therefore, I recommend using pip with the custom index
URL inside a clean environment (but you can run the ``pypi-timemachine``
command inside your regular environment.)


.. _simple-repository: https://github.com/simple-repository/

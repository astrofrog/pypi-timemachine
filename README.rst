A PyPI time machine
-------------------

Do you wish you could just install packages with pip as if you were at
some fixed date in the past? If so, the PyPI time machine is for you!

Installing
~~~~~~~~~~

To install::

   pip install pypi-timemachine

Using
~~~~~

Once installed, you can run a PyPI server with::

   pypi-timemachine 2014-02-03

or if you need to specify a precise time (in UTC)::

   pypi-timemachine 2014-02-03T12:33:02

This will start up a Flask app, and will print out a line such as::

   Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

You can then call pip with::

   pip install --index-url http://127.0.0.1:5000/ astropy

and this will then install the requested packages and all dependencies,
ignoring any releases after the cutoff date specified above.

Caveats/warnings
~~~~~~~~~~~~~~~~

If a package is already installed, pip will not try installing it again.
This means that if e.g. you try and run pip as described above, but the
package you are trying to install (or any of its dependencies) is
already installed, no matter how recent the version, it will not be
installed again. Therefore, I recommend using pip with the custom index
URL inside a clean environment (but you can run the ``pypi-timemachine``
command inside your regular environment.)

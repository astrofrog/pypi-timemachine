### A PyPI time machine

Do you wish you could just install packages as if you were at some fixed date
in the past? If so, the PyPI time machine is for you!

To install, clone this repository then:

    pip install .

Once installed, you can run a PyPI server with:

    pypi-timemachine 2014-02-03T00:00:00

This will start up a flask app, and will print out a line such as:

    Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

You can then call pip with:

    pip install --index-url http://127.0.0.1:5000/ astropy

and this will then install the requested packages and all dependencies, ignoring
any releases after the cutoff date specified above.

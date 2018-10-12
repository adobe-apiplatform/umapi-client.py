# umapi-client.py

This is a Python client for the User Management API from Adobe, aka the
[UMAPI](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

The User Management API is an Adobe-hosted network service 
which provides Adobe Enterprise customers the ability to manage their users.  This
client makes it easy to access the UMAPI from a local Python application.

This client is open source, maintained by Adobe, and distributed under the terms
of the OSI-approved MIT license.  Copyright (c) 2016-2017 Adobe Inc.

# Installation

You can get this package from PyPI: `pip install umapi-client`.
Or you can download the posted package from GitHub and use pip
to install from the download.

# Building

1. Clone this repository or download one of the posted releases.
2. From the command line, change to the `umapi-client.py` directory.
3. To install, run the command `python setup.py install`.
[**NOTE**: To avoid needing admin/root privileges for the installation
of needed dependencies,
it is recommended that you use `virtualenv` (or equivalent)
to make a virtual python environment.  See the
[virtualenvwrapper documentation](http://virtualenvwrapper.readthedocs.io/en/latest/index.html)
for more information.
4. Some of the packages required by this module use encryption, and so may
require you to do local builds of modules that use SSL.  Typically, this
will require you to have a python installed that supports compiling
extensions.
5. To run tests, use the command `python setup.py test`.

# Usage

Usage documentation, as well as information about how to get client
credentials for use of the UMAPI, can be found on the
[umapi-client wiki](https://adobe-apiplatform.github.io/umapi-client.py/),
whose sources are in the `docs` directory of this repository.


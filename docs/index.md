# umapi-client.py

This is a Python client for the User Management API from Adobe, aka the
[UMAPI](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

The User Management API is an Adobe-hosted network service
which provides Adobe Enterprise customers the ability to manage their users.  This
client makes it easy to access the UMAPI from a local Python application.

This client is open source, maintained by Adobe, and distributed under the terms
of the OSI-approved MIT license.  Copyright (c) 2016 Adobe Systems Incorporated.

# Installation

You can get this package from PyPI: `pip install umapi-client`.
Or you can download the posted package from GitHub and use pip
to install from the download.

# Building

1. Clone this repository or download the latest stable release.
2. From the command line, change to the `umapi-client.py` directory.
3. To install, run the command `python setup.py install`.
[**NOTE**: You may need admin/root privileges to install new packages in your environment.
It is recommended that you use `virtualenv` to make a virtual python environment.
See the [virtualenvwrapper documentation](http://virtualenvwrapper.readthedocs.io/en/latest/index.html)
for more information]
4. Some of the packages required by this module use encryption, and so may
require you to do local builds of modules that use SSL.  Typically, this
will require you to have to `python-dev` module installed (on all platforms),
and there may be other platform-specific requirements (e.g., on Mac OS X,
you will need to make sure the latest SSH libraries are on your LIBPATH.)
5. To run tests, use the command `python setup.py test`.

# Getting Started

Before making calls to the User Management API, you must do the following preparation steps:

1. Obtain admin access to an Adobe Enterprise Dashboard.
2. Set up a private/public certificate pair
3. Create an integration on [Adobe.IO](https://www.adobe.io/)

Step 1 is outside of the scope of this document.
Please contact your organization's administrator of your Dashbord environment to obtain access.
Steps 2 and 3 are outlined in the
[UMAPI documentation](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

Once access is obtained, and an integration is set up, you will need the following configuration items:

1. Organization ID
2. Tech Account ID
3. IMS Hostname
4. IMS Auth Token Endpoint (JWT Endpoint)
5. API Key
6. Client Secret
7. Private Key File (unencrypted form)

All but the last of these will be available on the adobe.io page for your integration.
The last one you should have on your local disk, and keep secret.

Once these initial steps are taken, and configuration items are identified,
then you will be able to use this library to make API calls.

# Usage Documentation

We are still working on the version 2 usage documentation.

You can find the version 1 documentation
[here](usage-instructions-v1.html).

---
layout: default
lang: en
version: v2
title: umapi-client.py - v2 Intro
nav_link: Intro
nav_order: 10
parent: root
page_id: v2-index
---

# umapi-client.py

This is a Python client for the User Management API from Adobe, aka the
[UMAPI](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

The User Management API is an Adobe-hosted network service
which provides Adobe Enterprise customers the ability to manage their users.  This
client makes it easy to access the UMAPI from a local Python application.

This client is open source, maintained by Adobe, and distributed under the terms
of the OSI-approved MIT license.  Copyright (c) 2016-2021 Adobe Inc.

# Installation

You can get this package from PyPI: `pip install umapi-client`.
Or you can download the desired release package
from [GitHub](https://github.com/adobe-apiplatform/umapi-client.py/)
and use pip to install from the download.

# Building

1. Clone
[the Github repository](https://github.com/adobe-apiplatform/umapi-client.py/)
or download one of
[the posted releases](https://github.com/adobe-apiplatform/umapi-client.py/releases).
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

# Getting Started

Before making calls to the User Management API, you must complete
the following preparatory steps:

1. Obtain admin access to an Adobe Enterprise Dashboard.
2. Set up a private/public key pair
3. Create an integration on [Adobe I/O](https://www.adobe.io/)

Step 1 is outside of the scope of this document.
Please contact an administrator of your organization's
Dashbord environment to obtain access.
Steps 2 and 3 are outlined in the
[UMAPI documentation](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

Once access is obtained, and an integration is set up,
you will need the following configuration values:

1. Organization ID
2. Tech Account ID
3. IMS Hostname
4. IMS Token Exchange Endpoint (aka JWT Endpoint)
5. API Key
6. Client Secret
7. Private Key File (unencrypted form)

All but the last of these will be available on the
[Adobe I/O page for your integration](https://www.adobe.io/console/integrations).
The last one you should have on your local disk, and keep secret.

Once these initial steps are taken, and configuration items are identified,
then you will be able to use this library to make API calls.

# umapi-client.py

This is a Python client for the User Management API from Adobe, aka the
[UMAPI](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

The User Management API is an Adobe-hosted network service 
which provides Adobe Enterprise customers the ability to manage their users.  This
client makes it easy to access the UMAPI from a local Python application.

This client is open source, maintained by Adobe, and distributed under the terms
of the OSI-approved MIT license.  Copyright (c) 2016-2021 Adobe Inc.

# Installation

`umapi-client.py` is published to the Python Packaging Index.

https://pypi.org/project/umapi-client/

It can be installed with pip:

```
$ pip install umapi-client
```

Or a dependency manager such as Poetry:

```
$ poetry add umapi-client
```

# Building

[Poetry](https://python-poetry.org/) is required to build the package. Follow the instructions documented on
Poetry's website to install it on your system.

1. Clone this repository
   ```
   $ git clone https://github.com/adobe-apiplatform/umapi-client.py
   $ cd umapi-client.py
   ```

2. Install dependencies to virtual environment.
   ```
   $ poetry install
   ```

3. The `build` command will create a source package (`.tar.gz`) and a wheel file (`.whl`) in the `dist` directory.
   ```
   $ poetry build
   $ ls dist
   umapi-client-2.18.tar.gz  umapi_client-2.18-py3-none-any.whl
   ```

4. Some of the packages required by this module use encryption, and so may
   require you to do local builds of modules that use SSL.  Typically, this
   will require you to have a python installed that supports compiling
   extensions.

5. Run tests with `pytest`.
   ```
   $ poetry run pytest
   ```

# Usage

Usage documentation, as well as information about how to get client
credentials for use of the UMAPI, can be found in the
[user guide](https://adobe-apiplatform.github.io/umapi-client.py/),
whose sources are in the `docs` directory of this repository.

# License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for more information.

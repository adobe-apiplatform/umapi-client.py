# cce-umapi
Python User Management API Interface for Creative Cloud Enterprise

# Installation

1. Clone this repository or download the latest stable release.
2. From the command line, change to the `cce-umapi` directory.
3. To install, run the command `python setup.py install`.  [**NOTE**: You may need admin/root privileges (using `sudo`) to install new packages in your environment.  It is recommended that you use `virtualenv` to make a virtual python environment.  See the [virtualenvwrapper documentation](http://virtualenvwrapper.readthedocs.io/en/latest/index.html) for more information]
4. If you encounter errors that repor missing library files, you may need to install the packages `python-dev`, `libssl-dev` and `libffi-dev` (these are the Debian package names - your environment may vary).
5. (**optional**) To run tests, use the command `python setup.py nosetests`.

# Getting Started

Before making calls to the User Management API, you must do the following preparation steps:

1. Obtain admin access to an Adobe Enterprise Dashboard.
2. Set up a private/public certificate pair
3. Create an integration on Adobe.io

Step 1 is outside of the scope of this document.  Please contact an administrator of your stage or prod Dashbord environment to obtain access.

Steps 2 and 3 are outlined in the documentaiton available at [adobe.io](http://www.adobe.io).

Once access is obtained, and an integration is set up, you will need the following configuration items:

1. Organization ID
2. Tech Account ID
3. IMS Hostname
4. IMT Auth Token Endpoint (JWT Endpoint)
5. API Key
6. Client Secret
6. Private Certificate

Most of this information should be availble on the adobe.io page for your integration.

Once these initial steps are taken, and configuration items are identified, then you will be able to use this library to make API calls.

## Step 1 - Create JSON Web Token

The JSON Web Token (JWT) is used to get an authorization token for using the API.  The `JWT` object will build the JWT for use with the `AccessRequest` object.

```python
from umapi.auth import JWT

jwt = JWT(
  org_id,     # Organization ID
  tech_acct,  # Techincal Account ID
  ims_host,   # IMS Host
  api_key,    # API Key
  open(priv_key_filename, 'r')  # Private certificate is passed as a file-like object
)
```

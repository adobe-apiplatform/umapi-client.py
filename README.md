# adobe-umapi.py

Python client for the Adobe User Management API, aka the
[Adobe UMAPI](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html)

# Installation

You can get this package from PyPI: `pip install adobe-umapi`.
Or you can download the posted package from GitHub and use pip
to install from the download.

(Note: as of 13 Dec 2016, there was an issue with the PyPI posting.
We are working to fix that problem.)

# Building

1. Clone this repository or download the latest stable release.
2. From the command line, change to the `adobe-umapi.py` directory.
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
3. Create an integration on Adobe.io

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
7. Private Certificate

Most of this information should be available on the adobe.io page for your integration.

Once these initial steps are taken, and configuration items are identified,
then you will be able to use this library to make API calls.

## Step 1 - Create JSON Web Token

The JSON Web Token (JWT) is used to get an authorization token for using the API.
The `JWT` object will build the JWT for use with the `AccessRequest` object.

```python
from adobe_umapi.auth import JWT

jwt = JWT(
  org_id,     # Organization ID
  tech_acct,  # Techincal Account ID
  ims_host,   # IMS Host
  api_key,    # API Key
  open(priv_key_filename, 'r')  # Private certificate is passed as a file-like object
)
```

## Step 2 - Use AccessRequest to Obtain Access Token

The `AccessRequest` object uses the JWT to call an IMS endpoint to obtain an access token.  This
token is then used in all later UMAPI calls to authenticate and authorize the request.

```python
from adobe_umapi.auth import AccessRequest

token = AccessRequest(
  "https://" + ims_host + ims_endpoint_jwt,   # Access Request Endpoint (IMS Host + JWT Endpoint)
  api_key,        # API Key
  client_secret,  # Client Secret
  jwt()           # JWT - note that the jwt object is callable - invoking it returns the JWT string expected by AccessRequest
)
```

The returned `token` is a Python _callable_ whose return value is an encoded form of
the token suitable for use to authenticate and authorize API calls.  The lifetime of
the token is typically 24 hours; its `token.expiry` attribute contains its expiration
date as a `datetime` object.

**NOTE**: You should _not_ generate a new token for each call.  Instead, continue
to use each generated token until it expires.

## Step 3 - The Auth Object

Once you have an access `token`, you use it to create an Auth object.  This Auth object
is used to build the necessary authentication headers for making an API call.

```python
from adobe_umapi.auth import Auth

auth = Auth(api_key, token())
```

## Step 4 - The UMAPI object

Once the `auth` object is built, you use it to construct a UMAPI object.  This UMAPI
object can then be used over and over to make your desired API calls.

```python
from adobe_umapi import UMAPI

api_endpoint = 'https://usermanagement.adobe.io/v2/usermanagement'
api = UMAPI(api_endpoint, auth)
```

# Querying for Users and Groups

These snippets presume you have constructed a UMAPI object named `api` as detailed in the last section.
The query APIs return data in paginated form, each page contaning up to 200 results.
The `adobe_umapi.helper`
module has a `paginate` utility which can will concatenate and return the results from all pages.

## Get a List of Users

```python
users = api.users(org_id, page=0)           # optional arg page defaults to 0

from adobe_umapi.helper import paginate
all_users = paginate(api.users, org_id)     # optional args for max_pages and max_records
```

## Get a List of Groups

This list of groups will contain both user groups and product license configuration groups.

```python
groups = api.groups(org_id, page=0)
all_groups = paginate(api.groups, org_id)
```

# Performing Actions on Users

To operate on a user we need an `Action` object, which encode both the user and
an action or group of actions to be performed on that user.
These actions include, but are not limited to, creation of users,
addition or removal of a user's product entitlements,
addition or removal of a user from a user group,
updating user attributes, and user deletion.

To create the action object, we name the user we wish to operate on.
(As above, `api` here in a UMAPI object.)

```python
from adobe_umapi import Action

action = Action(user="user@example.com")
```

We then record the actions we want to perform by calling
the `do` method of the created action.  For example,
given the `action` created above, we could record that
we want to create this user and add him to a user group
named 'group1':

```python
action.do(createAdobeID={"email": "user@example.com"})
action.do(add=['group1'])
```

And then we execute all the recorded actions with a single call:

```python
status = api.action(org_id, action)
```

**NOTE**: As you can see from the above, `do` is a side-effecting method, so it's
not necessary to use its return value.  But in fact it returns the action, and
it can take a sequence of keyword arguments, so both of the above operations
could have been record in one call, in either of two ways:

```python
action.do(createAdobeID={"email": "user@example.com"}).do(add=['group1'])
# or
action.do(createAdobeID={"email": "user@example.com"}, add=['group1'])
```

## Perform Actions on  Multiple Users

Multiple Action objects (each of which can perform multiple actions on a single user)
can be wrapped in some type of collection or iterable (typically a list)
and performed with a single call to `UMAPI.action`:

```python
actions = [
    Action(user="user@example.com").do(
        remove=["product1"]
    ),
    Action(user="user@example.com").do(
        add=["product2"]
    ),
]

status = api.action(org_id, actions)
```

# Library API Documentation

## Core Objects

### UMAPI

Main User Management API interface class.  Used to make calls to the API.

Requires endpoint URL and auth object.

Example:

```python
api = UMAPI(
  endpoint="https://usermanagement-stage.adobe.io/v2/usermanagement",
  auth=Auth( ... )
)
```

Any call made this this object can raise the `UMAPIError` and `UMAPIRetryError`.
`UMAPI.action` can additionally raise `UMAPIRequestError` for responses containing an error result type,
and `ActionFormatError` when an invalid action object is provided.

#### `UMAPI.users`

Get a list of users.

Requires the org_id.  Takes page number as an optional parameter (default=0).

Example:

```python
users = api.users(
  org_id="test_org_id",
  page=0
)['users']
```

The oject returned is the full API response object, which is a Python response object whose
`json` method is a Python serialization of the JSON response dictionary.
You will use the "users" key, which contains a list of dictionaries, each of which
holds the attributes of one user in the Adobe user directory.

Example "users" llist containing one user:

```python
[{
    u'status': u'active',
    u'firstname': u'Example',
    u'lastname': u'User',
    u'groups': [u'Example Group'],
    u'country': u'US',
    u'type': u'enterpriseID',
    u'email': u'user@example.com'
}]
```

The list returned by each page will contain up to 200 users.
The response object also contains the `lastPage` property,
which indicates if the end of the list has been reached.
If the organization contains more than 200 users,
then the `lastPage` property can be used to paginate through all user data
(by using the `page` parameter to `UMAPI.users`).  This is
what is done for you by `UMAPI.helper.paginate`.

#### `UMAPI.groups`

Get a list of permission/product entitlement groups.

Requires the org_id.  Takes page number as an optional parameter (default=0).

Example:

```python
groups = api.groups(
  org_id="test_org_id",
  page=0
)['groups']
```

The oject returned is the full API response object.
The main aspect is the "groups" key, which contains a list of all groups for the organization.

Example list of groups:

```python
[{
  u'memberCount': u'68',
  u'groupName': u'Administrators'
},{
  u'memberCount': u'4',
  u'groupName': u'Group 2'
}]
```

Like the `users` query, the response to a `groups` query is paginated.

#### `UMAPI.action`

Perform some kind of action - create users, add/remove groups, edit users, etc.
`UMAPI.action` depends on the Action object, which is detailed in the Action section of this documentation.

Requires both the org_id and action parameters.

Example:

```python
action = Action(user="user@example.com").do(
  update={"firstname": "Example", "lastname": "User"}
)
result = api.action(
  org_id="test_org_id",
  action=action
)
```

The result object returned is the complete result object returned by the User Management API.
If the response contains a result type of "error", then the action call will raise a `UMAPIRequestError`.
Success and partial result types do not raise any exceptions.

The exact format of the result object is detailed in
the [UMAPI documentation](https://www.adobe.io/products/usermanagement/docs/api/manageref).

### Action

The `Action` object models input to the UMAPI Management interface.
More specifically, it models an element of the action array that serves as the
top-level object to management calls.

Example:

```python
Action(user="user@example.com").do(
  addAdobeID={"email": "user@example.com"}
)
```

This Action object models the object needed to create an Adobe ID.  It is converted internally to this JSON:

```json
{
  "user": "user@example.com",
  "do": [
    {
      "addAdobeID": {
        "email": "user@example.com"
      }
    }
  ]
}
```

The Action object constructoe always requires the unique user ID,
but supports additional top-level ID properties such as `requestID` and `domain`.
It reads these attributes from `**kwargs` so there are no restrictions on which
of these attributes can be provided.

Example Python:

```python
Action(user="user", requestID="abc123", domain="example.com").do(
  createEnterpriseID={"email": "user@example.com"}
)
```

Equivalent JSON:

```json
{
  "user": "user",
  "requestID": "abc123",
  "domain": "example.com",
  "do": [
    {
      "addAdobeID": {
        "createEnterpriseID": "user@example.com"
      }
    }
  ]
}
```

#### `Action.do`

The `Action` object has one method - `do`.
This is used to define a list of actions to perform on the user for the call.

Like the object constructor, `do()` gets its parameters from `**kwargs`.
However, there are no required attributes.

The name of each `do()` argument should correspond to a key of the "do" container.
Those keys include "addAdobeID", "createEnterpriseID", "add", "remove", etc.
Refer to the [UMAPI reference](https://www.adobe.io/products/usermanagement/docs/api/overview)
for more details.

`do()` parameter values should be objects (strings, dicts, lists, etc) 
 structured in the way expected by the API.

Example:

```python
Action(user="user", domain="example.com").do(
  createEnterpriseID={"email": "user@example.com", "firstname": "Example", "lastname": "User"}
)
```

In the above example, the "createEnterpriseID" portion of the JSON would render like this:

```json
"createEnterpriseID": {"email": "user@example.com", "firstname": "Example", "lastname": "User"}
```

The exact structure of the `createEnterpriseID` parameter object is preserved.

There is one important exception - when using the "add" or "remove" actions,
which add/remove groups to/from the user account, `do()` will add the "product" wrapper.

Example:

```python
action = Action(user="user@example.com").do(
  add=["product1"]
)
```

Note that a list is being passed to the "add" parameter (instead of `{"product": ["product1"]}`).

The "add" portion of the JSON looks like this:

```json
"add": {"product": ["product1"]}
```

## adobe_umapi.auth

The submodule `adobe_umapi.auth` contains the components needed to build
the authentication headers needed for API communication.

### JWT

The `JWT` object builds the JSON Web Token needed to obtain an access token,
which is the security token needed for API call headers.

| Parameter | Type      | Required? | Notes                                                                    |
|-----------|-----------|-----------|--------------------------------------------------------------------------|
| org_id    | str       | Y         | Organization ID (found on Adobe.io integration page)                     |
| tech_acct | str       | Y         | Technical Account ID (found on Adobe.io integration page)                |
| ims_host  | str       | Y         | IMS Host - hostname of IMS endpoint (found on adobe.io integration page) |
| api_key   | str       | Y         | API Key (found on adobe.io integration page)                             |
| key_file  | file-like | Y         | File-like object that provides the private key (generated on server)     |

The `JWT` object is callable.  Calling it returns the encoded JWT.

Example:

```python
from adobe_umapi.auth import JWT

jwt = JWT(
  org_id,     # Organization ID
  tech_acct,  # Techincal Account ID
  ims_host,   # IMS Host
  api_key,    # API Key
  open(priv_key_filename, 'r')  # Private certificate is passed as a file-like object
)

encoded_jwt = jwt()
```

### AccessRequest

The `AccessRequest` object uses the JWT to make a request to IMS to retrieve an access token.

| Parameter     | Type      | Required? | Notes                                                                |
|---------------|-----------|-----------|----------------------------------------------------------------------|
| endpoint      | str       | Y         | Full IMS Endpoint URL                                                |
| api_key       | str       | Y         | API Key (found on Adobe.io integration page)                         |
| client secret | str       | Y         | Client Secret (found on adobe.io integration page)                   |
| jwt_token     | str       | Y         | Encoded JWT String (generated from JWT object)                       |

Like the `JWT` object, the `AccessRequest` object is callable.  Calling it returns the encoded access token string needed by the `Auth` object.

Basic Usage Example:

```python
from adobe_umapi.auth import AccessRequest

token = AccessRequest(
  "https://" + ims_host + ims_endpoint_jwt,   # Access Request Endpoint (IMS Host + JWT Endpoint)
  api_key,        # API Key
  client_secret,  # Client Secret
  jwt()           # JWT - note that the jwt object is callable - invoking it returns the JWT string expected by AccessRequest
)

token_str = token()
```

The `AccessRequest` object also has the propery `expiry`,
which is a [datetime](https://docs.python.org/2/library/datetime.html#datetime-objects) object
representing the date and time the access token expires.
It can be used with persistent token store systems to reduce the number of times a new token is required.

**NOTE**: The `expiry` attribute is not populated until the token is encoded
(i.e. the token object is called).

### Auth

The `Auth` object is used by the UMAPI object to build security headers for API calls.
It is a subclass of the
[requests auth.AuthBase class](http://docs.python-requests.org/en/master/user/authentication/#new-forms-of-authentication).

| Parameter    | Type | Required? | Notes                                                     |
|--------------|------|-----------|-----------------------------------------------------------|
| api_key      | str  | Y         | API Key (found on adobe.io integration page)              |
| access_token | str  | Y         | Access Token String (generated from AccessRequest object) |

Example:

```python
from adobe_umapi.auth import Auth

token = AccessRequest( ... )
auth = Auth(api_key, token())
```

## adobe_umapi.error

The `adobe_umapi.error` submodule contains all custom Exceptions for the UMAPI library.

### UMAPIError

Generic Error object that is raised when API returns non-retry or success
HTTP status code (i.e. 200, 429, 502, 503, 504).

### UMAPIRetryError

Error raised when a retry HTTP status code (429, 502, 503, 504).

See the [official documentation](https://www.adobe.io/products/usermanagement/docs/throttling)
for more information about handling this type of error.

### UMAPIRequestError

Error raised when an error status is reported from the API.
The API will return a 200 status code, but the JSON "result" status will be "error".

This currently only occurs when calling `UMAPI.action()`.

### ActionFormatError

Raised from `UMAPI.action()` when unexpected input is received from the `action` parameter.

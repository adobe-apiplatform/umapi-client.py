---
layout: default
lang: en
version: v3
title: umapi-client.py - Connecting
nav_link: Connection Setup
nav_order: 20
parent: root
page_id: v3-connecting
---

# Connection Setup
{:."no_toc"}

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

# Setting up a Connection

Setting up a connection is a two-step process.

1. Construct authenticator object
2. Use authenticator object to construct a connection object

> **Note**: The `auth_dict` option is no longer available as it was in `2.x` releases.
> Connections must be constructed with an authenticator object.

```python
from umapi_client.auth import JWTAuth
from umapi_client import Connection

jwt_auth = JWTAuth(...)

conn = Connection(org_id="your org id", auth=jwt_auth)
```

# JWT Service Account Authentication (`JWTAuth`)

The `JWTAuth` authenticator is designed to work with Service Account (JWT) credentials
created in the [Adobe Developer Console](https://developer.adobe.com/console/).

![](media/jwt_auth_cred.png)

It requires the Organization ID, Client ID, Client Secret and Tech Account ID that are
found on the credentials page. It additionally requires the contents of a private
key file associated with a public key that has been registered with the service.

```python
from umapi_client.auth import JWTAuth
from umapi_client import Connection

jwt_auth = JWTAuth(
  org_id="your org ID",
  client_id="your client ID",
  client_secret="your client secret",
  tech_acct_id="your technical account ID (not email)",
  priv_key_data="contents of the private key file (as string)",
)

conn = Connection(org_id="your org id", auth=jwt_auth)
```

## Additional `JWTAuth` Options

`JWTAuth`'s constructor supports a few optional parameters.

### `ssl_verify`

(default: `True`)

SSL verification can be optionally disabled if needed. This should only be done if
you are having trouble connecting to the UMAPI's authentication endpoint. Certain
network configurations may make it difficult or impossible to make a valid SSL
connection.

> It is always better to resolve connection issues in the environment. Use this
> option as a last resort.

During the calls, you will also see  a warning from requests:

```
InsecureRequestWarning: Unverified HTTPS request is being made to host
'ims-na1.adobelogin.com'. Adding certificate verification is strongly 
advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
```

### `auth_host`

(default: `ims-na1.adobelogin.com`)

Controls the authentication host. This setting should generally never need to
be changed.

### `auth_endpoint`

(default: `/ims/exchange/jwt/`)

Controls the authentication endpoint. This setting should generally never need to
be changed.

# Constructing New Connection

As described [above](#setting-up-a-connection), creating a UMAPI connection
requires two things.

* `org_id` - Organization ID of target Admin Console
* `auth` - Authenticator object

```python
from umapi_client.auth import JWTAuth
from umapi_client import Connection

jwt_auth = JWTAuth(...)

# keyword arguments
conn = Connection(org_id="your org id", auth=jwt_auth)

# no keyword arguments
conn = Connection("your org id", jwt_auth)
```

These parameters are described here, along with some optional connection
parameters.

## `org_id`

The `org_id` parameter should be set to the Organization ID tied to the Admin
Console organization this connection is targeting. This will be in the format
`12345@AdobeOrg`.

It can be found among the credentials for your UMAPI integration in the
[Adobe Developer Console](https://developer.adobe.com/console).

## `auth`

All UMAPI connections require an Authenticator object defined by the `auth` parameter.

This object must be either of these classes:

* [`JWTAuth`](#jwt-service-account-authentication-jwtauth) - legacy JWT Service
  Account authentication
* `ServicePrincipalAuth` (coming soon)

Each Authenticator requires its own set of credentials. Once constructed,
the auth object is passed to the `Connection` constructor:

```python
from umapi_client.auth import JWTAuth
from umapi_client import Connection

jwt_auth = JWTAuth(
  org_id="your org ID",
  client_id="your client ID",
  client_secret="your client secret",
  tech_acct_id="your technical account ID (not email)",
  priv_key_data="contents of the private key file (as string)",
)

conn = Connection(org_id="your org id", auth=jwt_auth)
```

## `endpoint`

(default: `https://usermanagement.adobe.io/v2/usermanagement`)

Customize the API endpoint with the `endpoint` parameter. Most UMAPI
clients will not require this, but the option is available for
use under certain circumstances.

## `test_mode`

(default: `False`)

Engage the UMAPI's special "dry run" mode, which permits the client to
make test calls that would normally make changes to user state.

For example, if we were to get a count of existing users before
and after creating a user in test mode, the second count will
match the first count.

```python
from umapi_client.auth import JWTAuth
from umapi_client import Connection, UsersQuery, UserAction

auth = JWTAuth(...)
conn = Connection('12345@AdobeOrg', auth, test_mode=True)

count_before = len(UsersQuery(conn).all_results())
conn.execute_single(UserAction(...).create(...), True)
count_after = len(UsersQuery(conn).all_results())

assert count_before == count_after
```

See the [UMAPI Documentation](https://adobe-apiplatform.github.io/umapi-documentation/en/api/ActionsRef.html#using-test-mode)
for more info.

## `timeout`

(default: `120`)

`timeout` governs the maxmimum time (in seconds) the underlying HTTP client
waits before terminating a connection. 

More information [here](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts).

## `ssl_verify`

(default: `True`)

Disable SSL verification. This should only be done if you are having trouble
connecting to the UMAPI's authentication endpoint. Certain network
configurations may make it difficult or impossible to make a valid SSL
connection.

> It is always better to resolve connection issues in the environment. Use this
> option as a last resort.

During the calls, you will also see  a warning from requests:

```
InsecureRequestWarning: Unverified HTTPS request is being made to host
'usermanagement.adobe.io'. Adding certificate verification is strongly 
advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
```

# Connection Methods

## `status`

`status()` returns a tuple consisting of a local status and remote status.

* Local - statistics describing what kinds of actions have been perfomed by the
  UMAPI client so far.
  
  ```
  >>> conn = Connection(...)
  >>> local, _ = conn.status()
  >>> local
  {"multiple-query-count": 5, "single-query-count": 1, "actions-sent": 25, "actions-completed": 20, "actions-queued": 5}
  ```
  
* Remote - current status of UMAPI service. Passing the argument `remote=True`
  will trigger the client to make a live status call to the API service.
  Otherwise the cached status is returned (or a special message if the status
  hasn't yet been retrieved).
  
  Example with `remote=True`:
  
  ```
  >>> conn = Connection(...)
  >>> _, remote = conn.status(remote=True)
  >>> remote
  {"status": {"build": "d1d82f1e94503d7ba93872c34deda5037aa4a73d", "version": "2.7.42", "side": "A", "environment": "jil-prod-ue1", "state":"LIVE"}, "endpoint": "https://usermanagement.adobe.io/v2/usermanagement"}
  ```
  
  Without `remote=True`:
  
  ```
  >>> conn = Connection(...)
  >>> _, remote = conn.status()
  >>> remote
  {"status": "Never contacted", "endpoint": "https://usermanagement.adobe.io/v2/usermanagement"}
  ```
## `execute_single`


## `execute_multiple`
## `execute_queued`

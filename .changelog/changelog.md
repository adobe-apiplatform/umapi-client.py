| tag    | date       | title               |
|--------|------------|---------------------|
| v3.0.1 | 2023-07-20 | umapi-client v3.0.1 |

# Fixes

* d22a6c4 Suppress log messages - can be enabled by library consumer if desired

---

| tag | date | title |
|---|---|---|
| v3.0 | 2023-05-18 | umapi-client v3.0 |

# Changes in Version 3

This is a major release and contains many compatibility-breaking changes. Chief
among these is an ovehaul of the auth layer and the the introduction of the
`OAuthS2S` auth class which authenticates UMAPI clients using
[Server-to-Server](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/implementation/)
authentication. JWT-based authentication functionality is deprecated.

Refer to the user guide for details:

https://adobe-apiplatform.github.io/umapi-client.py/v3/

## Summary of Changes

- Authentication Interface
  - New `AuthBase` to cover basic auth functionality
  - Old JWT stuff rolled into single `JWTAuth` class
  - New `OAuthS2S` class representing new Server-to-Server authentication method
- Connection Interface
  - Removed `auth_dict` functionality
  - `AuthBase`-derived object must be passed to `Connection` constructor via
    `auth` parameter
  - Removed `ims_host` and `ims_endpoint_jwt` - these are `AuthBase` attributes
  - `user_management_endpoint` renamed to `endpoint`
  - Removed `logger` param
  - Changes to timeout and retry constructor params
    - Renamed `retry_max_attempts` to `max_retries`
    - Removed `retry_first_delay`
    - Removed `retry_random_delay`
    - `timeout_seconds` renamed to `timeout`
  - Removal of "throttling" params
    - `throttle_actions`
    - `throttle_commands`
    - `throttle_groups`
- Removed Deprecated Enums
  - `GroupTypes`
  - `RoleTypes`
- Enum Naming Tweaks
  - `IdentityTypes` -> `IdentityType`
  - `IfAlreadyExistsOptions` -> `IfAlreadyExistsOption`
- `UserAction` Changes
  - Constructor Updates
    - Replaced `email` and `username` params with `user` param that models the
      `user` field in a UMAPI action command object. This can be username or
      email address depending on context.
    - Removed `id_type` field. Identity type is only needed when creating a new
      user.
    - Refactor some validation to `create()`
  - `create()` Updates
    - `email` is now mandatory
    - Add `id_type` parameter
    - Perform some validation that was done in the constructor
  - `update()` Updates
    - Country code is not a valid user update parameter
  - `add_to_groups()` Updates
    - It isn't possible to assign a user to all group
    - Group type is deprecated
  - `remove_from_groups()` Updates
    - Group type is deprecated
  - `add_role()` and `remove_role()` were removed because role-based
    functionality is deprecated in the API
  - Country code removed from `update()` because UMAPI does not support
    country code updates
- `UserQuery` Updates
  - Change `email` param in constructor to `user_string` to reflect UMAPI
    terminology. Add `domain` parameter which is supported by UMAPI.
- `UsersQuery` Updates
  - Remove `identity_type` parameter from constructor. The UMAPI has never
    supported filtering users by identity type.
- Rename `UserGroupAction` to `GroupAction`
- `GroupAction` Changes
  - `products` paramter in `add_to_products()` and `remove_from_products()` is
    mandatory
  - It isn't possible to add all products to a group or remove all (without
    enumerating every product profile in `products`)
  - `users` parameter in `add_users()` and `remove_users()` is mandatory
- `UserGroupsQuery` class removed because the `user-group` UMAPI endpoint does
  not exist
- Deleted `legacy.py`

---

| tag | date | title |
|---|---|---|
| v2.22 | 2023-03-07 | umapi-client v2.22 |

- 4a5773f allow username to be updated by itself

---

| tag | date | title |
|---|---|---|
| v2.21 | 2022-12-14 | umapi-client v2.21 |

- 3c3d725 buid with newer poetry and drop 3.6 build
- c65be58 upgrade to newer version of cryptography
- 74e8c1e remove old docs
- f8dda00 #104 removing test\_delete\_account\_enterpriseid and test\_delete\_account\_adobeid
- bd701c4 #104 remove removeFromDomain action

---

| tag | date | title |
|---|---|---|
| v2.20 | 2022-08-05 | umapi-client v2.20 |

* \#103 Create users with email-type usernames that differ from email address in a single call

---

| tag | date | title |
|---|---|---|
| v2.19 | 2022-03-08 | umapi-client v2.19 |

* \#98 Add X-Request-Id header to all calls
* \#100 Send start/end headers on any type of call

---

| tag | date | title |
|---|---|---|
| v2.18 | 2021-08-23 | umapi-client v2.18 |

Bug fixes and new start/end sync signals

* \#89 Logging updates
* \#92 Fix bad return causing ValueError
* \#94 Add hooks for start/end sync signals

---

| tag | date | title |
|---|---|---|
| v2.17.1 | 2021-04-16 | umapi-client v2.17.1 |

No updates to functionality, just changes to the build system.

* \#90 Switch from setup.py to Poetry

---

| tag | date | title |
|---|---|---|
| v2.17 | 2021-01-29 | umapi-client v2.17 |

* \#84 Pin dependencies and fix jwt issue
* \#85 create changelog
* \#86 CI config updates

---

| tag | date | title |
|---|---|---|
| v2.16 | 2021-01-22 | umapi-client v2.16 |

\#83 - Implement `ssl_verify` for authentication endpoint

---

| tag | date | title |
|---|---|---|
| v2.15 | 2020-10-28 | umapi-client v2.15 |

\#75 Add statistics from response headers for query_multiple
\#79 Treat connection error like a timeout
\#80 & \#81 Switch CI platforms

---

| tag | date | title |
|---|---|---|
| v2.14 | 2020-04-30 | umapi-client v2.14 |

\#76 Option to disable SSL validation for UMAPI calls

---

| tag | date | title |
|---|---|---|
| v2.13 | 2019-11-14 | umapi-client v2.13 |

* Make `group` the default key for group operations
* Only install `enum34` if Python version < 3.4

---

| tag | date | title |
|---|---|---|
| v2.12 | 2019-01-09 | umapi-client v2.12 |

Modify validation behavior to facilitate the creation of users that may have different email addresses and email-type usernames.

---

| tag | date | title |
|---|---|---|
| v2.11 | 2018-08-31 | umapi-client v2.11 |

Supports the creation, deletion, and updating of Adobe groups.  Supports the assignment of large lists of groups that will be split into lists no larger than 10 apiece, according to the UMAPI spec.

---

| tag | date | title |
|---|---|---|
| v2.10 | 2017-12-08 | Enhancement: UMAPI_MOCK environment variable |

The new environment variable `UMAPI_MOCK` controls whether the umapi_client can be used with a mock server: either a `proxy` server which accepts http and relays requests to the actual server via https, recording requests and responses; or a `playback` server which accepts http, doesn't require auth, and simply plays back the server answers from a prior run.  Both these modes are used by the user_sync test_framework.

---

| tag | date | title |
|---|---|---|
| v2.9 | 2017-11-14 | Bug fix: Better UMAPI limits checking |

The UMAPI limits the number of groups (or roles) that can be added or removed to a user in a single action step to 10, but the umapi-client was not checking for that limit and splitting action steps as necessary to stay within it.  Now it does.

---

| tag | date | title |
|---|---|---|
| v2.8 | 2017-10-18 | Compatibility fixes for UMAPI changes |

Because the UMAPI functionality around Adobe IDs is now different for migrated organizations, the client no longer does a lot of redundant validation of server-side checks.  This makes it more tolerant of clients who use it against both migrated and non-migrated orgs.

**NOTE**: Clients that were relying on the umapi-client to default Enterprise ID country code to "UD" now need to specify it themselves.

* [Issue 54](https://github.com/adobe-apiplatform/umapi-client.py/issues/54)
    * Allow setting attributes on Adobe ID users as long as the server allows it.
* [Issue 55](https://github.com/adobe-apiplatform/umapi-client.py/issues/55)
    * Don't default the country code when creating new Enterprise ID users.

---

| tag | date | title |
|---|---|---|
| v2.7 | 2017-08-26 | Better unicode fixes! |

The fix for #50 used in v2.6 had problems, so this fixes it better.  (See #50 for details.)  Because we have introduced a new error `ArgumentError` which is a subclass of `ValueError`, this release gets a full dot rather than a double dot.

---

| tag | date | title |
|---|---|---|
| v2.6 | 2017-08-05 | Unicode fixes |

This is a bug fix release aimed at fixing error messages related to invalid Unicode input.  Without these fixes, clients cannot handle the error strings being returned.  (See #50 for details.)

---

| tag | date | title |
|---|---|---|
| v2.5.2 | 2017-06-16 | minor enhancement to v2.5.1 |

This release reads the wall clock to return an accurate "total time" in the `UnavailableError` (and associated logging).  It's an improvement to the fix of #47, but it has no separate issue.

---

| tag | date | title |
|---|---|---|
| v2.5.1 | 2017-06-16 | minor bug fix on v2.5 |

There was a logging issue on timeouts (#47) that is fixed in this release.

---

| tag | date | title |
|---|---|---|
| v2.5 | 2017-05-10 | allow control of group membership info returned by UsersQuery |

The results of UsersQuery include group memberships for all returned users.  The server API includes a query flag that controls whether this membership information includes only direct memberships, or also includes indirect memberships in product configurations that contain user groups that contain the user.  But umapi-client was not exposing control over this flag.  This release exposes the server's _directOnly_ query parameter as direct_only boolean flag to the UsersQuery initializer.  The default value of the flag is `True`, meaning only include direct memberships in the returned data.

---

| tag | date | title |
|---|---|---|
| v2.4.1 | 2017-05-04 | Fast follow bug fix for v2.4 validation issues |

This tightens up the validation of Unicode emails and usernames introduced in v2.4 so it matches the validation performed by Adobe's UMAPI server.  It also fixes a cosmetic issue with validation error messages.  See issue #42 for details.

---

| tag | date | title |
|---|---|---|
| v2.4 | 2017-05-04 | Handle unicode strings in Python 2.7 |

This is a bug fix release for #42.  It correctly handles Python 2.7 clients who use Unicode strings.

---

| tag | date | title |
|---|---|---|
| v2.3 | 2017-04-17 | Security enhancement release |

This release adds the ability for clients to specify their private key data directly when creating a connection, as opposed to having to put it in a local file.  Thus it allows removing the chance of someone else on the machine observing the file content.  For details, see the documentation of `Connection.__init__`, in particular the new `private_key_data` argument.

This release also adds certification for Python 2.6 support.

---

| tag | date | title |
|---|---|---|
| v2.2 | 2017-03-29 | Error handling for user sync |

This release adds better error handling during processing of actions in batches: when the server response is not understood, the client doesn't throw except at the end of the batch, and the error thrown contains the usual return statistics from the batch processing.

---

| tag | date | title |
|---|---|---|
| v2.1 | 2017-03-24 | v2.1 - match evolution of the server API |

This is a very small release, but necessary to match evolution of the server API around removing users from organizations and deleting their user accounts. It's numbered 2.1 rather than 2.0.4 so the name looks cleaner in a requirements file for clients who are seeing the new server behavior.

---

| tag | date | title |
|---|---|---|
| v2.0.3 | 2017-02-22 | Network timeout enhancements |

Enhancement release:
- Issue #32
  - change timeout default to 2 minutes
  - add retry after timeout.
  - change default create behavior to "ignoreIfAlreadyExists"
- (No issue)
  - fix misspellings
  - change .gitignore so that .gitignore is not ignored

---

| tag | date | title |
|---|---|---|
| v2.0.2 | 2017-02-02 | User-Agent header enhancements |

Add a User-Agent header with version information to all server requests, and make it possible for clients to add their User-Agent info to the header.

---

| tag | date | title |
|---|---|---|
| v2.0.1 | 2017-01-17 | Release 2.0.1 with fixes for #27, #28. |

This release fixes issues discovered by user-sync development, optimizes via connection reuse, and improves the documentation around creating UserAction objects.

---

| tag | date | title |
|---|---|---|
| v2.0 | 2017-01-13 | umapi-client 2.0GM |

Public release of v2 of the umapi-client.  This release contains a functional layer and connection enhancements that completely shield the application writer from protocol issues.

You can install the release from [PyPI/umapi-client](https://pypi.python.org/pypi?:action=display&name=umapi-client&version=2.0) with `pip install --upgrade umapi-client`.

---

| tag | date | title |
|---|---|---|
| v2.0rc1 | 2017-01-05 | First release candidate for 2.0 |

Now with support for python 2.7, 3.4, 3.5, and Travis CI support/posting to PyPI.

---

| tag | date | title |
|---|---|---|
| v2.0b2 | 2016-12-27 | Release beta 2 |

With better legacy support and a brand new documentation wiki,
we are getting close to a release candidate for v2.  There's a bit
more work to do on the v2 usage docs first.

---

| tag | date | title |
|---|---|---|
| v2.0b1 | 2016-12-25 | Release 2.0b1 |

This is a massive overhaul of the v1 code.  It includes:
- better connection management.
- umapi_client automated throttling and batching of all calls, with app-level controls.
- functional wrappers for all the server API calls.
- queries that iterate
- preservation of legacy compatibility in the umap_client.legacy module.

---

| tag | date | title |
|---|---|---|
| v1.0.1 | 2016-12-17 | Release the fix of #12 |

OMG!  That has to be the shortest-lived 1.0 release ever!

This pushes the fix of #12 to PyPI.  I have also removed the older postings.

---

| tag | date | title |
|---|---|---|
| v1.0.0 | 2016-12-17 | Finally, a v1 production release! |

After many renames and typo fixes, we are finally at our v1 release.  Yay!

---

| tag | date | title |
|---|---|---|
| v1.0.0rc5 | 2016-12-17 | Updated ReadMe |

---

| tag | date | title |
|---|---|---|
| v1.0.0rc4 | 2016-12-16 | Yet another rename! |

This time to the final, Adobe-approved name, which ironically doesn't have Adobe in it!

So now we are at rc4, and I expect this will become 1.0.0 later today!  Fingers crossed!! 👍 

---

| tag | date | title |
|---|---|---|
| v1.0.0rc3 | 2016-12-14 | Copyrights added. |

Fixes #4, which was the only blocker for release.  Putting out what is hopefully the final candidate.

This also brands the adobe.io short link in the setup.py description of the module.

---

| tag | date | title |
|---|---|---|
| v1.0.0rc2 | 2016-12-14 | rename complete - next release candidate |

This is expected to be the final release, barring any bugs found in final testing.  The naming has been updated, and the build is [posted on PyPI](https://pypi.python.org/pypi/adobe-umapi-client/1.0.0rc2/).

---

| tag | date | title |
|---|---|---|
| v1.0.0rc1 | 2016-12-13 | everything done but the naming |

This was going to be the content of the first release, but then we decided to name the published object differently.  This one is functionally complete, has full smoke-testing, and runs on Python 2.7.x and 3.5.x.

---
layout: default
lang: en
version: v3
title: umapi-client.py - API Queries
nav_link: Queries
nav_order: 30
parent: root
page_id: v3-queries
---

# Querying UMAPI
{:."no_toc"}

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

# Querying Users

User and group queries (see below) are handled with special classes. These
classes perform user/group retrieval and, if necessary, pagination.

Two classes provide user query functionality:

- `UserQuery` - Query a single user.
- `UsersQuery` - Query multiple users by group or organization.

## `UserQuery`

Use the `UserQuery` class to get a single user by user string. If the user
is found, it is returned in dictionary format.

Here, **User String** is defined as either the user's email or username,
depending on identity type. Email should be specified to find an Adobe ID
or Enterprise ID account. Federated IDs can alternatively be queried by
username as long as it is in an email-like format (e.g. user@domain).
Non-email must also supply domain in the `domain` parameter (see below).

```python
from umapi_client import JWTAuth, Connection, UserQuery

auth = JWTAuth(...)
conn = Connection(auth=auth...)

# email or email-type username
user = UserQuery(conn, "user@example.com").result()

# non-email username
user = UserQuery(conn, "user", "example.com").result()

if user is not None:
    print(user)
```

The `result()` method returns a dictionary representing the user. Exmaple:

```python
{
    'id': '12345@9876',
    'email': 'user@example.com',
    'status': 'active',
    'groups': ['Default All Apps - 1024 GB configuration'],
    'username': 'user@example.com',
    'domain': 'example.com',
    'orgSpecific': True,
    'businessAccount': True,
    'firstname': 'Test',
    'lastname': 'User',
    'country': 'US',
    'type': 'federatedID'
}
```

`result()` returns `None` if no user is found for the given user string.

If you need to re-run the same user query, the `reload()` method will force
the query to re-run the next time `result()` is called.

## `UsersQuery`

The `UsersQuery` class is used to query users in an Admin Console organization
or group.

With no additional parameters (apart from `connection`) the query will return
all users for the organization defined in the connection.

```python
from umapi_client import JWTAuth, Connection, UsersQuery

auth = JWTAuth(...)
conn = Connection(auth=auth...)

users = UsersQuery(conn)
for user in users:
    print(user)
```

In this use case, all users in the organization are returned regardless of group
membership or domain. The iterable constructed by `UsersQuery` returns a dictionary
record for each user, following the same structure as `UserQuery.result()`.

> **Note:** Users in any `UsersQuery` result list represent users present in the `Users`
> tab in the admin console. Users present in a directory but not in the console user
> list are not included.

Use the `in_group` parameter to restrict the query to members of a specific group.

```python
# get all users belonging to group "All Apps"
users = UsersQuery(conn, in_group="All Apps")
```

`UserQuery` also supports some additional optional parameters.

* `in_domain` - Filter result to include only members of a specific domain. The domain
  must be claimed to a directory owned by the organization specified in the connection.

* `direct_only` - If `True`, the `groups` field will only contain groups to which the
  user belongs directly. Otherwise indirect memberships will also be included, such as
  profiles that are granted via a user group association.

# Querying Groups

Groups and product profiles can be queried in a manner similar to users. Unlike users,
there is no way to query a single group. The UMAPI only supports getting a full list
of groups from the organization.

> **Note:** The word "group" is used here to refer to either product profiles,
> special admin groups, or user groups, unless otherwise specified.

To query groups with the client, construct a `GroupsQuery` object.

```python
from umapi_client import JWTAuth, Connection, GroupsQuery

auth = JWTAuth(...)
conn = Connection(auth=auth...)

groups = GroupsQuery(conn)
for group in groups:
    print(group)
```

Each group is returned as a dictionary (as with user objects). The fields present
in a group dictionary can vary depending on group type. This is an example of a
product profile:

```python
{
  "groupId": 316396208,
  "groupName": "Default All Apps - 1024 GB configuration",
  "type": "PRODUCT_PROFILE",
  "adminGroupName": "_admin_Default All Apps - 1024 GB configuration",
  "memberCount": 17,
  "productName": "All Apps (ETLA)",
  "licenseQuota": "100"
}
```

Any group should have four attributes:

* `groupId` - numeric ID of group
* `groupName` - alphanumeric group or profile name
* `type` - group type, one of:
  * `USER_GROUP`
  * `PRODUCT_PROFILE`
  * `SYSADMIN_GROUP`
  * `DEPLOYMENT_ADMIN_GROUP`
  * `SUPPORT_ADMIN_GROUP`
  * `PRODUCT_ADMIN_GROUP`
  * `PROFILE_ADMIN_GROUP`
  * `USER_ADMIN_GROUP`
  * `DEVELOPER_GROUP`
* `memberCount` - number of users assigned to the group

Groups may also possess other attributes which may vary depending on the group
type.

* `adminGroupName` - For profiles and user groups, this contains the name of the
  corresponding group that governs group/profile admin privileges for the group.
* `productName` - For profiles this contains the name of the product associated
  with the profile. Also provided for product admin groups.
* `licenseQuota` - The allocation of licenses for a product profile.
* `profileGroupName` - The name of the product profile associated with a profile
  admin group.

---

**Previous**: [Connection Setup](connecting.md)

**Next**: [Managing Users and Groups](managing.md)

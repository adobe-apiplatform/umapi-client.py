---
layout: default
lang: en
version: v3
title: umapi-client.py - Managing Users and Groups
nav_link: Managing Users and Groups
nav_order: 40
parent: root
page_id: v3-managing
---

# Managing Users and Groups
{:."no_toc"}

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

# Overview

The User Management API handles the creation, update and removal of users and
groups via a single endpoint. It is documented
[here](https://adobe-apiplatform.github.io/umapi-documentation/en/api/ActionsRef.html)
in the UMAPI docs.

`umapi-client.py` provides an interface to this endpoint with the `UserAction`
and `GroupAction` objects as well as the `Connection.execute_*()` methods.

The UMAPI actions endpoint accepts user actions in batches of up to 10 actions
per call. Each action represents a series of one or more commands on an
individual user. Certain rules govern how actions and commands work in
conjunction.

The `Action` classes and `Connection` methods mentioned earlier are set up to
batch actions as efficiently as possibl, and manage actions and commands based
on factors such as number of assigned groups.

# Managing Users

The class `UserAction` defines operations to perform on a single user. This
includes user creation, user information update, group/product profile
management and user removal or deletion.

Actions are handled in the client in three steps:

1. Identify the user with the `user` parameter. This should be email address
   or username depending on which actions are planned.
   
   * `user` should be set to a user's username if this will be a `create`
     operation.
   * Otherwise, `user` should be set to the user's email address.
   
   > **Note:** If you plan to create a user and perform more operations (e.g.
   > group management) on the user, the `user` field should still be set to
   > username.

   ```python
   from umapi_client import UserAction
   
   # use email when operating on existing user
   user = UserAction(user="user@example.com")
   user.update(...)
   
   # use username when creating a new user
   user = UserAction(user="username@domain.local")
   user.create(...)
   
   # provide domain for non-email username
   user = UserAction(user="username", domain="domain.local")
   user.create(...)
   ```

2. Define one or more operations to perform on the user.

   ```python
   from user_sync import UserAction
   
   user = UserAction(user="username@domain.local")
   user.create(email="user@example.com")
   user.add_to_groups(groups=['group1', 'group2'])
   ```

3. Queue Action for Execution

   ```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction(...)
   user.create(...)
   
   # execute_single() queues an action for processing
   # immediate=True immediately post the action to UMAPI
   conn.execute_single(user, immediate=True)
   ```

## Creating Users

There are two things to remember when creating a user.

1. The `UserAction` object should be created with the user's username if the
   username differs from the user's email address. This should be done even
   when you plan to add other actions on the same user (e.g. create user
   and then assign groups) before executing it.
2. Invoke the `create()` method to specify user details.
  - `email` - Email address of user
  - `firstname` - User's given name
  - `lastname` - User's surname
  - `country` - User's [two-letter ISO-3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
  - `id_type` (default: Federated ID) - User's identity type. For ESM environments, this should be the
    user's linked account type.
 
### Basic Example

This creates a user with the default identity type (Federated ID).

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("test.username@example.com")
   user.create(
     email="test.email@example.com",
     firstname"Test",
     lastname"User",
     country="GB",
   )
   conn.execute_single(user, immediate=True)
```

### Identity Types

To specify the identity type when creating a user, use the `IdentityType` enum.

```python
   from user_sync import UserAction, Connection, IdentityType

   conn = Connection(...)
   user = UserAction("test.username@example.com")
   user.create(
     email="test.email@example.com",
     firstname"Test",
     lastname"User",
     country="GB",
     # default: IdentityType.federatedID
     # also accepted: IdentityType.adobeID
     id_type=IdentityType.enterpriseID,
   )
   conn.execute_single(user, immediate=True)
```

## Updating User Information

User information (First Name, Last Name, etc) can be updated using the
`update()` method. When updating users, the `UserAction` should be constructed
with the user's email address (unless creating the user before updating it).

The following parameters are accepted by `update()`. All are optional.

- `email` - Email address of user
- `username` - User's username
- `firstname` - User's given name
- `lastname` - User's surname

### Basic Example

If updating the user's email address, then `UserAction` should be constructed
with the user's **current** email address, not the new address.

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("sal.smith@example.com")
   user.update(
     lastname"Jones",
     email="sal.jones@example.com",
   )
   conn.execute_single(user, immediate=True)
```

## Group Membership

Groups for an individual user are managed with `add_to_groups()` and
`remove_from_groups()`.

Both methods take a `group` parameter to specify one or more groups to
add/remove.

- `groups` - List of groups to add/remove. Should be a list of group names,
  not group IDs. Group names in the admin console are treated as unique
  identifiers (without respect to letter case).

`remove_from_groups()` also supports an option to remove a user from all
assigned groups.

- `all_groups` - Set to `True` if you want to remove the user from all
assigned groups. Cannot be used in conjunction with `groups`.

These methods support all group types - product profile, user group and admin
role. See [the UMAPI documentation](https://adobe-apiplatform.github.io/umapi-documentation/en/api/ActionsCmds.html#addRemoveAttr)
for more information.

### Adding Groups Example

As with `update()`, the user's email should be used when constructing
`UserAction`.

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("test.email@example.com")
   user.add_to_groups(
     groups=["Group A", "Group B"]
   )
   conn.execute_single(user, immediate=True)
```

Admin roles and other special groups can be assigned in the same mechanism.

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("test.email@example.com")
   user.add_to_groups(
     groups=["Group A", "_support_admin"]
   )
   conn.execute_single(user, immediate=True)
```

### Group Removal Example

Users can be removed from specific groups.

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("test.email@example.com")
   user.remove_from_groups(
     groups=["Group A"]
   )
   conn.execute_single(user, immediate=True)
```

It is also possible to remove a user from all assigned groups without passing a
list of those groups.

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("test.email@example.com")
   user.remove_from_groups(
     all_groups=True
   )
   conn.execute_single(user, immediate=True)
```

## Removing Users

The UMAPI client supports two different methods of user removal.

- **Soft deletion** - this option will remove a user from the Adobe organization
  associated with the API connection. This means the user will no longer appear
  in the Users list in the console UI and the user account will not be assigned
  any groups or product entitlements.
  
  Soft-deleted users still belong to the underlying identity directory. This
  directory account may still be associated with users in other organizations
  (orgs that have a trust relationship with the one you are targeting).
  
  Soft deletion can be performed on any user of any type, on any organization,
  regardless of whether or not that organization owns the underlying identity
  directory that contains the user.
  
- **Hard deletion** - hard deletion entails the removal of a user from an
  identity directory. This means that hard deletion operations can't be
  performed on Adobe ID users, nor is it permitted on organizations that don't
  own the directory associated with a user. Hard deletion can only be performed
  under the these conditions:
  
  - You are making the UMAPI call to an organization that owns one or more
    federated or enterprise directories
  - You are removing a user that belongs to one of those owned directories
  
  Hard deletion is permanent and irreversible. When performed on a user
  belonging to a User Storage Management (USM) console, any cloud assets or
  libraries owned by the user are also subject to immediate removal. Assets for
  hard-deleted users under the Enterprise Storage Model (ESM) are not removed.
  They are instead set up for deferred transfer.

Either method can be invoked with the `remove_from_organization()` method.
Soft deletion is performed with no parameters. To hard-delete, pass the option
`delete_account=True`.

### Example

The `UserAction` for a removal should be constructed with the user's email
address.

```python
   from user_sync import UserAction, Connection

   conn = Connection(...)
   user = UserAction("test.email@example.com")
   
   # to soft delete, do not pass the "delete=True" option
   user.remove_from_organization()
   
   # "delete=True" will perform a hard-delete
   user.remove_from_organization(delete=True)

   conn.execute_single(user, immediate=True)
```

# Managing Groups

The User Management API supports the creation, maintenance and removal of user
groups. Unlike other contexts involving groups, this functionality does not
extend to product profiles or special admin groups (e.g. `_org_admin`). Product
profiles can only be managed in the Admin Console UI and special groups are
either built-in or are automatically generated (e.g. profile or product admin
groups).

## The `GroupAction` Object

`GroupAction` objects are analagous to `UserAction` objects except that they
specify actions to be performed on groups instead of users.

The following methods are supported.

 - `create()` - create a new user group
 - `update()` - update the name and/or description of an existing user group
 - `delete()` - delete a user group
 - `add_users()` - add users to a user group
 - `remove_users()` - remove users from a user group
 - `add_to_products()` - add one or more product profiles to a user group
 - `remove_from_products()` - remove one or more product profiles from a user group
 
`GroupName` objects must be constructed with the name of the group. This can be
the name of an existing group or the name of the group you wish to create.

```python
group = GroupAction("My Group")
```

## Creating Groups

The `create()` method creates a new user group.
<!-- def create(self, option=IfAlreadyExistsOption.ignoreIfAlreadyExists, description=None): -->

```python
   from user_sync import GroupAction, Connection, IfAlreadyExistsOption

   conn = Connection(...)
   group = GroupAction("Example Group")
   group.create()
   conn.execute_single(group, immediate=True)
```

An optional description can be provided to let others know the purpose of the group.

```python
   from user_sync import GroupAction, Connection, IfAlreadyExistsOption

   conn = Connection(...)
   group = GroupAction("Example Group")
   group.create(description="This is a demonstration group")
   conn.execute_single(group, immediate=True)
```

The `option` parameter governs behavior when calling create() on an existing
group. Valid values are anything implemented in the `IfAlreadyExistsOption` enum.

 - `ignoreIfAlreadyExists` - Ignore the `create()` command, doing nothing and
   returning no error
 - `updateIfAlreadyExists` - Update the group with new description if one is
   provided
 - `errorIfAlreadyExists` - Raise an error if the group already exists

```python
   from user_sync import IfAlreadyExistsOption
   
   group.create(
     option=IfAlreadyExistsOption.updateIfAlreadyExists,
     description="New group description",
   )
```

## Updating Groups

The `update()` method can update the name and/or description of a group. To
update either or both of these items, the `GroupAction` object must be
constructed with the name of the group as it currently exists.

```python
   from user_sync import GroupAction, Connection

   conn = Connection(...)
   group = GroupAction("Current Group Name")
   group.update(
     name="Updated Group Name",
     description="Updated group description",
   )
   conn.execute_single(group, immediate=True)
```

## Deleting Groups

Groups can be deleted with the `delete()` method. To delete a group, construct
`GroupAction` with the current group name and simple invoke the delete method.
It takes no paramters.

```python
   from user_sync import GroupAction, Connection

   conn = Connection(...)
   group = GroupAction("My Group")
   group.delete()
   conn.execute_single(group, immediate=True)
```

## Managing Users/Profiles

In addition to basic creation, updating and deletion of groups, the UMAPI
supports managing users at the group level and managing the product profiles
that are associated with groups.

### Managing Users in Groups

The group management functionality of the UMAPI supports the addition and
removal of users to and/from groups.

To to add users to a group, use the `add_users()` method. `add_users()` takes a
list of email addresses representing the users to add to the group.

```python
   from user_sync import GroupAction, Connection

   conn = Connection(...)
   group = GroupAction("My Group")
   
   # the list must contain email addresses of users to add, not usernames
   group.add_users([
     "test.user.01@example.com",
     "test.user.02@example.com",
     "test.user.03@example.com",
   ])

   conn.execute_single(group, immediate=True)
```

Removals are performed in a similar manner using the `remove_users()` method.

```python
   from user_sync import GroupAction, Connection

   conn = Connection(...)
   group = GroupAction("My Group")
   
   # the list must contain email addresses of users to add, not usernames
   group.remove_users([
     "test.user.02@example.com",
   ])

   conn.execute_single(group, immediate=True)
```

### Managing Profiles in Groups
<!-- def add_to_products(self, products): -->
<!-- def remove_from_products(self, products): -->

The UMAPI has the ability to manage the product profiles associated with a user
group. This is done using the `add_to_products()` and `remove_from_products()`
methods.

> **Note:** The UMAPI can't assign product profiles that don't exist. Be sure to
> create any profiles needed in the Admin Console UI, as the UMAPI lacks any
> capability to manage product profiles directly outside of user group
> assignment.

`add_to_products()` example:

```python
   from user_sync import GroupAction, Connection

   conn = Connection(...)
   group = GroupAction("All Apps Users")
   
   # the list must contain the exact product profile name, irrespective of
   # letter case
   group.add_to_products([
     "Default All Apps - 1024 GB configuration",
   ])

   conn.execute_single(group, immediate=True)
```

`remove_from_products()` example:

```python
   from user_sync import GroupAction, Connection

   conn = Connection(...)
   group = GroupAction("All Apps Users")
   
   # the list must contain the exact product profile name, irrespective of
   # letter case
   group.remove_from_products([
     "Photoshop",
   ])

   conn.execute_single(group, immediate=True)
```

---

**Previous**: [User and Group Queries](queries.md)

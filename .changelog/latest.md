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

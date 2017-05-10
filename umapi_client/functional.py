# Copyright (c) 2016-2017 Adobe Systems Incorporated.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
from enum import Enum

import six

from .api import Action, QuerySingle, QueryMultiple


class IdentityTypes(Enum):
    adobeID = 1
    enterpriseID = 2
    federatedID = 3


class GroupTypes(Enum):
    product = 1
    # group = product  # deprecated!
    usergroup = 2


class RoleTypes(Enum):
    admin = 1
    productAdmin = 2


class IfAlreadyExistsOptions(Enum):
    ignoreIfAlreadyExists = 1
    updateIfAlreadyExists = 2
    errorIfAlreadyExists = 3


class UserAction(Action):
    """
    A sequence of commands to perform on a single user.
    """

    # regex patterns to be compiled once and used in _validate
    # The RFC6531 extended syntax for email addresses allows Unicode alphanumerics in the local part,
    # but the Adobe identity system doesn't support that extended syntax for user account emails.
    # This is the RFC-allowed pattern:
    # _atext_pattern = r"(\w|[!#$%&'*+/=?^_`{|}~;-])+"
    # This is the one allowed by Adobe:
    _atext_pattern = r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+"
    _local_pattern = _atext_pattern + r"([.]" + _atext_pattern + ")*"
    _dns_pattern = r"[a-zA-Z0-9-]+([.][a-zA-Z0-9-]+)+"
    _email_regex = re.compile(r"\A" + _local_pattern + r"@" + _dns_pattern + r"\Z", re.UNICODE)
    _username_regex = re.compile(r"^" + _local_pattern + r"$", re.UNICODE)
    _domain_regex = re.compile(r"^" + _dns_pattern + r"$", re.UNICODE)

    @classmethod
    def _validate(cls, email=None, username=None, domain=None):
        '''
        Validates the specified user attributes against their specifications.
        Input values must be strings (standard or unicode).  Throws ValueError if any input is invalid
        :param email: an email address
        :param username: a username
        :param domain: a domain
        '''
        if email and not cls._email_regex.match(email):
            email = email.encode('utf-8')
            raise ValueError("'%s': Illegal email format (must be ascii, unquoted, with no comment part)" % (email,))
        if domain and not cls._domain_regex.match(domain):
            domain = domain.encode('utf-8')
            raise ValueError("'%s': Illegal domain format" % (domain,))
        if username and not cls._username_regex.match(username):
            username = username.encode('utf-8')
            raise ValueError("'%s': Illegal username format (must be unquoted email local part)" % (username,))

    def __init__(self, id_type=IdentityTypes.adobeID, email=None, username=None, domain=None, **kwargs):
        """
        Create an Action for a user identified either by email or by username and domain.
        You should pretty much always use just email, unless the user has a Federated ID and his
        username is different from his email.  In that case you can give either username and email
        (and we'll get the domain from his email) or the username and domain (in case you don't
        know or don't care about the user's email).
        Note that the identity type determines what you can do with this user.  For example,
        create will create a user of the specified identity type.  Similarly, each identity type restricts
        what fields can be updated.  If you are specifying an existing user by email, and you are not
        sure what identity type the existing user is, and you are doing something (such as add_to_groups)
        that can be done with any identity type, then you can specify any type, and the type you specify
        will be used to break ties if there is both an AdobeID and an EnterpriseID or FederatedID user
        with that same email.  Normally, we choose Enterprise ID or Federated ID *over* Adobe ID, but
        if you specify the type as Adobe ID then we will act on the Adobe ID user instead.
        :param id_type: IdentityTypes enum value (or the name of one), defaults to adobeID
        :param email: The user's email.  Typically this is also the user's username.
        :param username: The username on the Adobe side.  If it's the same as email, it's ignored.
        :param domain: string, needed only if you specified a username but NOT an email.
        :param kwargs: other key/value pairs for the action, such as requestID
        """
        if id_type in IdentityTypes.__members__:
            id_type = IdentityTypes[id_type]
        if id_type not in IdentityTypes:
            raise ValueError("Identity type ({}}) must be one of {}}".format(id_type, [i.name for i in IdentityTypes]))
        self.id_type = id_type
        self.email = None
        self.domain = None
        if username:
            if email and username.lower() == email.lower():
                # ignore the username if it's the same as the email (policy default)
                username = None
            elif id_type is not IdentityTypes.federatedID:
                raise ValueError("Username must match email except for Federated ID")
            else:
                self._validate(username=username)
                if domain:
                    self._validate(domain=domain)
                    self.domain = domain
        if email:
            self._validate(email=email)
            self.email = email
            if not self.domain:
                atpos = email.index('@')
                self.domain = email[atpos + 1:]
        elif not username:
            raise ValueError("No user identity specified.")
        elif not domain:
            raise ValueError("Both username and domain must be specified")
        if username:
            Action.__init__(self, user=username, domain=self.domain, **kwargs)
        elif id_type == IdentityTypes.adobeID:
            # by default if two users have the same email address, the UMAPI server will prefer the matching
            # Federated or Enterprise ID user; so we use the undocumented option to prefer the AdobeID match
            Action.__init__(self, user=email, useAdobeID=True, **kwargs)
        else:
            Action.__init__(self, user=email, **kwargs)

    def create(self, first_name=None, last_name=None, country=None, email=None,
               on_conflict=IfAlreadyExistsOptions.ignoreIfAlreadyExists):
        """
        Create the user on the Adobe back end.
        See [Issue 32](https://github.com/adobe-apiplatform/umapi-client.py/issues/32): because
        we retry create calls if they time out, the default conflict handling for creation is to ignore the
        create call if the user already exists (possibly from an earlier call that timed out).
        :param first_name: (optional) user first name
        :param last_name: (optional) user last name
        :param country: (optional except for Federated ID) user 2-letter ISO country code
        :param email: user email, if not already specified at create time
        :param on_conflict: IfAlreadyExistsOption (or string name thereof) controlling creation of existing users
        :return: the User, so you can do User(...).create(...).add_to_groups(...)
        """
        # all types handle email and on_conflict similarly
        create_params = {}
        if email is None:
            email = self.email
        elif self.email is None:
            self._validate(email=email)
            self.email = email
        elif self.email.lower() != email.lower():
            raise ValueError("Specified email ({}) doesn't match user's email({})", email, self.email)
        if on_conflict in IfAlreadyExistsOptions.__members__:
            on_conflict = IfAlreadyExistsOptions[on_conflict]
        if on_conflict not in IfAlreadyExistsOptions:
            raise ValueError("on_conflict must be one of {}".format([o.name for o in IfAlreadyExistsOptions]))
        if on_conflict != IfAlreadyExistsOptions.errorIfAlreadyExists:
            create_params["option"] = on_conflict.name

        # each type handles the create differently
        if self.id_type == IdentityTypes.adobeID:
            # Adobe ID doesn't allow anything but email
            if first_name or last_name or country:
                raise ValueError("You cannot specify first or last name or country for an Adobe ID.")
            return self.insert(addAdobeID=dict(email=email, **create_params))
        else:
            # Federated and Enterprise allow specifying the name
            if first_name: create_params["firstname"] = first_name
            if last_name: create_params["lastname"] = last_name
            if self.id_type == IdentityTypes.enterpriseID:
                # Enterprise ID can default country, already has email on create
                create_params["country"] = country if country else "UD"
                return self.insert(createEnterpriseID=dict(email=email, **create_params))
            else:
                # Federated ID must specify email if that wasn't done already
                if not email:
                    raise ValueError("You must specify email when creating a Federated ID")
                if not country:
                    raise ValueError("You must specify country when creating a Federated ID")
                return self.insert(createFederatedID=dict(email=email, country=country, **create_params))

    def update(self, email=None, username=None, first_name=None, last_name=None, country=None):
        """
        Update values on an existing user.  See the API docs for what kinds of update are possible.
        :param email: new email for this user
        :param username: new username for this user
        :param first_name: new first name for this user
        :param last_name: new last name for this user
        :param country: new country for this user
        :return: the User, so you can do User(...).update(...).add_to_groups(...)
        """
        if self.id_type is IdentityTypes.adobeID:
            raise ValueError("You cannot update any attributes of an Adobe ID.")
        if email: self._validate(email=email)
        if username and self.id_type is IdentityTypes.enterpriseID:
            self._validate(email=username)
        updates = {}
        for k, v in six.iteritems(dict(email=email, username=username,
                                       firstname=first_name, lastname=last_name,
                                       country=country)):
            if v: updates[k] = v
        return self.append(update=updates)

    def add_to_groups(self, groups=None, all_groups=False, group_type=None):
        """
        Add user to some (typically PLC) groups.  Note that, if you add to no groups, the effect
        is simply to do an "add to organization Everybody group", so we let that be done.
        :param groups: list of group names the user should be added to
        :param all_groups: a boolean meaning add to all (don't specify groups or group_type in this case)
        :param group_type: the type of group (defaults to "product")
        :return: the User, so you can do User(...).add_to_groups(...).add_role(...)
        """
        if all_groups:
            if groups or group_type:
                raise ValueError("When adding to all groups, do not specify specific groups or types")
            glist = "all"
        else:
            if not groups:
                groups = []
            if not group_type:
                group_type = GroupTypes.product
            elif group_type in GroupTypes.__members__:
                group_type = GroupTypes[group_type]
            if group_type not in GroupTypes:
                raise ValueError("You must specify a GroupType value for argument group_type")
            glist = {group_type.name: [group for group in groups]}
        return self.append(add=glist)

    def remove_from_groups(self, groups=None, all_groups=False, group_type=None):
        """
        Remove user from some PLC groups, or all of them.
        :param groups: list of group names the user should be removed from
        :param all_groups: a boolean meaning remove from all (don't specify groups or group_type in this case)
        :param group_type: the type of group (defaults to "product")
        :return: the User, so you can do User(...).remove_from_groups(...).add_role(...)
        """
        if all_groups:
            if groups or group_type:
                raise ValueError("When removing from all groups, do not specify specific groups or types")
            glist = "all"
        else:
            if not groups:
                raise ValueError("You must specify groups from which to remove the user")
            if not group_type:
                group_type = GroupTypes.product
            elif group_type in GroupTypes.__members__:
                group_type = GroupTypes[group_type]
            if group_type not in GroupTypes:
                raise ValueError("You must specify a GroupType value for argument group_type")
            glist = {group_type.name: [group for group in groups]}
        return self.append(remove=glist)

    def add_role(self, groups=None, role_type=RoleTypes.admin):
        """
        Make user have a role (typically PLC admin) with respect to some PLC groups.
        :param groups: list of group names the user should have this role for
        :param role_type: the role (defaults to "admin")
        :return: the User, so you can do User(...).add_role(...).add_to_groups(...)
        """
        if not groups:
            raise ValueError("You must specify groups to which to add the role for this user")
        if role_type in RoleTypes.__members__:
            role_type = RoleTypes[role_type]
        if role_type not in RoleTypes:
            raise ValueError("You must specify a RoleType value for argument role_type")
        glist = {role_type.name: [group for group in groups]}
        return self.append(addRoles=glist)

    def remove_role(self, groups=None, role_type=RoleTypes.admin):
        """
        Remove user from a role (typically admin) of some groups.
        :param groups: list of group names the user should NOT have this role for
        :param role_type: the type of role (defaults to "admin")
        :return: the User, so you can do User(...).remove_role(...).remove_from_groups(...)
        """
        if not groups:
            raise ValueError("You must specify groups from which to remove the role for this user")
        if role_type in RoleTypes.__members__:
            role_type = RoleTypes[role_type]
        if role_type not in RoleTypes:
            raise ValueError("You must specify a RoleType value for argument role_type")
        glist = {role_type.name: [group for group in groups]}
        return self.append(removeRoles=glist)

    def remove_from_organization(self, delete_account=False):
        """
        Remove a user from the organization's list of visible users.  Optionally also delete the account.
        Deleting the account can only be done if the organization owns the account's domain.
        :param delete_account: Whether to delete the account after removing from the organization (default false)
        :return: None, because you cannot follow this command with another.
        """
        self.append(removeFromOrg={"deleteAccount": True if delete_account else False})
        return None

    def delete_account(self):
        """
        Delete a user's account.
        Deleting the user's account can only be done if the user's domain is controlled by the authorized organization,
        and removing the account will also remove the user from all organizations with access to that domain.
        :return: None, because you cannot follow this command with another.
        """
        if self.id_type == IdentityTypes.adobeID:
            raise ValueError("You cannot delete an Adobe ID account.")
        self.append(removeFromDomain={})
        return None


class UsersQuery(QueryMultiple):
    """
    Query for users meeting (optional) criteria
    """

    def __init__(self, connection, in_group="", in_domain="", identity_type="", direct_only=True):
        """
        Create a query for all users, or for those in a group or domain or both
        :param connection: Connection to run the query against
        :param in_group: (optional) name of the group to restrict the query to
        :param in_domain: (optional) name of the domain to restrict the query to
        """
        groups = [in_group] if in_group else []
        params = {}
        if in_domain: params["domain"] = in_domain
        if identity_type: params["type"] = identity_type
        params["directOnly"] = direct_only
        QueryMultiple.__init__(self, connection=connection, object_type="user", url_params=groups, query_params=params)


class UserQuery(QuerySingle):
    """
    Query for a single user
    """

    def __init__(self, connection, email):
        """
        Create a query for the user with the given email
        :param connection: Connection to run the query against
        :param email: email of user to query for
        """
        QuerySingle.__init__(self, connection=connection, object_type="user", url_params=[email])


class UserGroupAction(Action):
    """
    A sequence of commands to perform on a single user group.
    """

    def __init__(self, group_name=None, **kwargs):
        """
        Create an Action for a user group identified either by name.
        :param group_name: string, name of the group
        :param kwargs: other key/value pairs for the action, such as requestID
        """
        if not group_name:
            ValueError("You must provide the name of the group")
        Action.__init__(self, usergroup=group_name, **kwargs)

    def add_to_products(self, products=None, all_products=False):
        """
        Add user group to some product license configuration groups (PLCs), or all of them.
        :param products: list of product names the user should be added to
        :param all_products: a boolean meaning add to all (don't specify products in this case)
        :return: the Group, so you can do Group(...).add_to_products(...).add_users(...)
        """
        if all_products:
            if products:
                raise ValueError("When adding to all products, do not specify specific products")
            plist = "all"
        else:
            if not products:
                raise ValueError("You must specify products to which to add the user group")
            plist = {GroupTypes.product.name: [product for product in products]}
        return self.append(add=plist)

    def remove_from_products(self, products=None, all_products=False):
        """
        Remove user group from some product license configuration groups (PLCs), or all of them.
        :param products: list of product names the user group should be removed from
        :param all_products: a boolean meaning remove from all (don't specify products in this case)
        :return: the Group, so you can do Group(...).remove_from_products(...).add_users(...)
        """
        if all_products:
            if products:
                raise ValueError("When removing from all products, do not specify specific products")
            plist = "all"
        else:
            if not products:
                raise ValueError("You must specify products from which to remove the user group")
            plist = {GroupTypes.product.name: [product for product in products]}
        return self.append(remove=plist)

    def add_users(self, users=None):
        """
        Add users (specified by email address) to this user group.
        In case of ambiguity (two users with same email address), the non-AdobeID user is preferred.
        :param users: list of emails for users to add to the group.
        :return: the Group, so you can do Group(...).add_users(...).add_to_products(...)
        """
        if not users:
            raise ValueError("You must specify emails for users to add to the user group")
        ulist = {"user": [user for user in users]}
        return self.append(add=ulist)

    def remove_users(self, users=None):
        """
        Remove users (specified by email address) from this user group.
        In case of ambiguity (two users with same email address), the non-AdobeID user is preferred.
        :param users: list of emails for users to remove from the group.
        :return: the Group, so you can do Group(...).remove_users(...).add_to_products(...)
        """
        if not users:
            raise ValueError("You must specify emails for users to remove from the user group")
        ulist = {"user": [user for user in users]}
        return self.append(remove=ulist)


class GroupsQuery(QueryMultiple):
    """
    Query for all groups
    """

    def __init__(self, connection):
        """
        Create a query for all groups
        :param connection: Connection to run the query against
        """
        QueryMultiple.__init__(self, connection=connection, object_type="group")

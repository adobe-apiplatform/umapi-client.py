# Copyright (c) 2016-2021 Adobe Inc.  All rights reserved.
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

from .api import Action, QuerySingle, QueryMultiple
from .error import ArgumentError, UnsupportedError


class IdentityType(Enum):
    adobeID = 1
    enterpriseID = 2
    federatedID = 3


class IfAlreadyExistsOption(Enum):
    ignoreIfAlreadyExists = 1
    updateIfAlreadyExists = 2
    errorIfAlreadyExists = 3


class UserAction(Action):
    """
    A sequence of commands to perform on a single user.
    """

    def __init__(self, user, domain=None, use_adobe_id=False, **kwargs):
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
        :param user: Primary user identifier. Should be username for "create" operations or email address otherwise
        :param domain: Domain of non-email username
        :param kwargs: other key/value pairs for the action, such as requestID
        """
        if '@' not in user and domain is None:
            raise ArgumentError("Domain required for non-email username")
        if '@' in user and domain is not None:
            raise ArgumentError("Domain not allowed for email-type username")
        if domain is not None:
            kwargs['domain'] = domain
        if use_adobe_id:
            kwargs['useAdobeID'] = True
        super().__init__(user=user, **kwargs)

    def __str__(self):
        return "UserAction "+str(self.__dict__)

    def __repr__(self):
        return "UserAction "+str(self.__dict__)

    def create(self, email, first_name=None,
               last_name=None, country=None, id_type=IdentityType.federatedID,
               on_conflict=IfAlreadyExistsOption.ignoreIfAlreadyExists):
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
        if id_type in IdentityType.__members__:
            id_type = IdentityType[id_type]
        if id_type not in IdentityType:
            raise ArgumentError("Identity type (%s) must be one of %s" % (id_type, [i.name for i in IdentityType]))
        # first validate the params: email, on_conflict, first_name, last_name, country
        create_params = {}
        create_params["email"] = email
        if on_conflict in IfAlreadyExistsOption.__members__:
            on_conflict = IfAlreadyExistsOption[on_conflict]
        if on_conflict not in IfAlreadyExistsOption:
            raise ArgumentError("on_conflict must be one of {}".format([o.name for o in IfAlreadyExistsOption]))
        if on_conflict != IfAlreadyExistsOption.errorIfAlreadyExists:
            create_params["option"] = on_conflict.name
        if first_name: create_params["firstname"] = first_name
        if last_name: create_params["lastname"] = last_name
        if country: create_params["country"] = country

        # each type is created using a different call
        if id_type == IdentityType.adobeID:
            self.frame['useAdobeID'] = True
            return self.insert(addAdobeID=dict(**create_params))
        elif id_type == IdentityType.enterpriseID:
            return self.insert(createEnterpriseID=dict(**create_params))
        else:
            return self.insert(createFederatedID=dict(**create_params))

    def update(self, email=None, username=None, first_name=None, last_name=None):
        """
        Update values on an existing user.  See the API docs for what kinds of update are possible.
        :param email: new email for this user
        :param username: new username for this user
        :param first_name: new first name for this user
        :param last_name: new last name for this user
        :return: the User, so you can do User(...).update(...).add_to_groups(...)
        """
        updates = {}
        for k, v in dict(email=email, username=username,
                         firstname=first_name, lastname=last_name).items():
            if v:
                updates[k] = v
        return self.append(update=updates)

    def add_to_groups(self, groups=list()):
        """
        Add user to one or more groups
        :param groups: list of group names the user should be added to
        :return: the User, so you can do User(...).add_to_groups(...).???()
        """
        glist = {"group": [group for group in groups]}
        return self.append(add=glist)

    def remove_from_groups(self, groups=None, all_groups=False):
        """
        Remove user from some PLC groups, or all of them.
        :param groups: list of group names the user should be removed from
        :param all_groups: a boolean meaning remove from all (don't specify groups)
        :return: the User, so you can do User(...).remove_from_groups(...).???(...)
        """
        if all_groups:
            if groups:
                raise ArgumentError("When removing from all groups, do not specify specific groups")
            glist = "all"
        else:
            if not groups:
                raise ArgumentError("You must specify groups from which to remove the user")
            glist = {"group": [group for group in groups]}
        return self.append(remove=glist)

    def remove_from_organization(self, delete_account=False):
        """
        Remove a user from the organization's list of visible users.  Optionally also delete the account.
        Deleting the account can only be done if the organization owns the account's domain.
        :param delete_account: Whether to delete the account after removing from the organization (default false)
        :return: None, because you cannot follow this command with another.
        """
        self.append(removeFromOrg={"deleteAccount": True if delete_account else False})
        return None


class UsersQuery(QueryMultiple):
    """
    Query for users meeting (optional) criteria
    """

    def __init__(self, connection, in_group="", in_domain="", direct_only=True):
        """
        Create a query for all users, or for those in a group or domain or both
        :param connection: Connection to run the query against
        :param in_group: (optional) name of the group to restrict the query to
        :param in_domain: (optional) name of the domain to restrict the query to
        """
        groups = [in_group] if in_group else []
        params = {}
        if in_domain: params["domain"] = in_domain
        params["directOnly"] = direct_only
        QueryMultiple.__init__(self, connection=connection, object_type="user", url_params=groups, query_params=params)


class UserQuery(QuerySingle):
    """
    Query for a single user
    """

    def __init__(self, connection, user_string, domain=None):
        """
        Create a query for the user with the given user_string (email or username)
        :param connection: Connection to run the query against
        :param user_string: user string identifying a user
        """
        qparam = {}
        if domain is not None:
            qparam['domain'] = domain
        QuerySingle.__init__(self, connection=connection, object_type="user", url_params=[user_string], query_params=qparam)


class UserGroupAction(Action):
    """
    A sequence of commands to perform on a single user group.
    """

    _group_name_regex = re.compile(r'^[^_]')
    _group_name_length = 255

    @classmethod
    def _validate(cls, group_name):
        """
        Validates the group name
        Input values must be strings (standard or unicode).  Throws ArgumentError if any input is invalid
        :param group_name: name of group
        """
        if group_name and not cls._group_name_regex.match(group_name):
            raise ArgumentError("'%s': Illegal group name" % (group_name,))
        if group_name and len(group_name) > 255:
            raise ArgumentError("'%s': Group name is too long" % (group_name,))

    def __init__(self, group_name=None, **kwargs):
        """
        Create an Action for a user group identified either by name.
        :param group_name: string, name of the group
        :param kwargs: other key/value pairs for the action, such as requestID
        """
        if not group_name:
            ArgumentError("You must provide the name of the group")
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
                raise ArgumentError("When adding to all products, do not specify specific products")
            plist = "all"
        else:
            if not products:
                raise ArgumentError("You must specify products to which to add the user group")
            plist = {"productConfiguration": [product for product in products]}
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
                raise ArgumentError("When removing from all products, do not specify specific products")
            plist = "all"
        else:
            if not products:
                raise ArgumentError("You must specify products from which to remove the user group")
            plist = {"productConfiguration": [product for product in products]}
        return self.append(remove=plist)

    def add_users(self, users=None):
        """
        Add users (specified by email address) to this user group.
        In case of ambiguity (two users with same email address), the non-AdobeID user is preferred.
        :param users: list of emails for users to add to the group.
        :return: the Group, so you can do Group(...).add_users(...).add_to_products(...)
        """
        if not users:
            raise ArgumentError("You must specify emails for users to add to the user group")
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
            raise ArgumentError("You must specify emails for users to remove from the user group")
        ulist = {"user": [user for user in users]}
        return self.append(remove=ulist)

    def create(self, option=IfAlreadyExistsOption.ignoreIfAlreadyExists, description=None):
        # only validate name on create/update so we can allow profiles and users to be managed for
        # system groups
        self._validate(self.frame['usergroup'])
        create_command_exists = bool([c for c in self.commands if c.get('createUserGroup', None)])
        if create_command_exists:
            raise ArgumentError("Only one create() operation allowed per group command entry")
        create_params = {'option': option.name}
        if description:
            create_params['description'] = description
        return self.insert(createUserGroup=dict(**create_params))

    def update(self, name=None, description=None):
        self._validate(name)
        update_params = {}
        if name:
            update_params['name'] = name
        if description:
            update_params['description'] = description
        return self.append(updateUserGroup=dict(**update_params))

    def delete(self):
        delete_params = {}
        return self.append(deleteUserGroup=dict(**delete_params))


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


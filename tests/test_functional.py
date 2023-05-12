# coding: utf-8

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

import pytest

from conftest import MockResponse
from umapi_client import ArgumentError, RequestError
from umapi_client import Connection
from umapi_client import IdentityType
from umapi_client import UserAction, GroupAction
from umapi_client import UsersQuery


def test_user_emptyid():
    with pytest.raises(TypeError):
        UserAction()


def test_user_adobeid():
    user = UserAction(user="user@example.com", use_adobe_id=True)
    assert user.wire_dict() == {"do": [],
                                "user": "user@example.com",
                                "useAdobeID": True}


def test_user_define():
    user = UserAction(user="user@example.com")
    assert user.wire_dict() == {"do": [], "user": "user@example.com"}


def test_user_username():
    user = UserAction(user="username", domain="domain.local")
    assert user.wire_dict() == {"do": [], "user": "username", "domain": "domain.local"}


def test_create_user_adobeid():
    user = UserAction(user="user@example.com")
    user.create(email="user@example.com", id_type=IdentityType.adobeID)
    assert user.wire_dict() == {"do": [{"addAdobeID": {"email": "user@example.com",
                                                       "option": "ignoreIfAlreadyExists"}}],
                                "user": "user@example.com",
                                "useAdobeID": True}


def test_create_user_adobeid_country():
    user = UserAction(user="user@example.com")
    user.create(email="user@example.com", country="US", id_type=IdentityType.adobeID)
    assert user.wire_dict() == {"do": [{"addAdobeID": {"email": "user@example.com",
                                                       "country": "US",
                                                       "option": "ignoreIfAlreadyExists"}}],
                                "user": "user@example.com",
                                "useAdobeID": True}


def test_create_user_enterpriseid():
    user = UserAction(user="user@example.com")
    user.create(email="user@example.com", first_name="Example", last_name="User",
                id_type=IdentityType.enterpriseID)
    assert user.wire_dict() == {"do": [{"createEnterpriseID": {"email": "user@example.com",
                                                               "firstname": "Example", "lastname": "User",
                                                               "option": "ignoreIfAlreadyExists"}}],
                                "user": "user@example.com"}


def test_create_user_federatedid():
    user = UserAction(user="user@example.com")
    user.create(email="user@example.com", first_name="Example", last_name="User",
                country="US", id_type=IdentityType.federatedID)
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "user@example.com",
                                                              "firstname": "Example", "lastname": "User",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "user@example.com"}

    user = UserAction(user="user@example.com")
    user.create(email="user@example.com", first_name="Example", last_name="User",
                country="US")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "user@example.com",
                                                              "firstname": "Example", "lastname": "User",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "user@example.com"}


def test_create_user_federatedid_username():
    user = UserAction(user="user", domain="example.com")
    user.create(first_name="Example", last_name="User", country="US", email="user@example.com")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "user@example.com",
                                                              "firstname": "Example", "lastname": "User",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "user", "domain": "example.com"}


def test_create_user_username_no_domain():
    with pytest.raises(ArgumentError):
        user = UserAction(user="user")


def test_create_user_email_username_domain():
    with pytest.raises(ArgumentError):
        user = UserAction(user="user@example.com", domain="example.com")


def test_different_email_username():
    # pass username to identify user on create
    user = UserAction(user="user.username@example.com")
    user.create(email="user.email@example.com", first_name="User", last_name="Name", country="US")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "user.email@example.com",
                                                              "firstname": "User",
                                                              "lastname": "Name",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "user.username@example.com"}


def test_update_user_adobeid():
    user = UserAction(user="user@example.com", use_adobe_id=True)
    user.update(first_name="User Updated", last_name="Name Updated")
    assert user.wire_dict() == {"do": [{"update": {"firstname": "User Updated", "lastname": "Name Updated"}}],
                                "user": "user@example.com",
                                "useAdobeID": True}


def test_update_user():
    user = UserAction(user="user@example.com")
    user.update(first_name="User Updated", last_name="Name Updated")
    assert user.wire_dict() == {"do": [{"update": {"firstname": "User Updated", "lastname": "Name Updated"}}],
                                "user": "user@example.com"}


def test_update_username():
    # pass email to identify user
    user = UserAction(user="user.email@example.com")
    user.update(username="user.username@example.com")
    assert user.wire_dict() == {"do": [{"update": {"username": "user.username@example.com"}}],
                                "user": "user.email@example.com"}


def test_add_org():
    user = UserAction(user="user@example.com")
    user.add_to_groups()
    assert user.wire_dict() == {"do": [{"add": {"group": []}}],
                                "user": "user@example.com"}


def test_add_products():
    user = UserAction(user="user@example.com")
    user.add_to_groups(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"add": {"group": ["Photoshop", "Illustrator"]}}],
                                "user": "user@example.com"}


def test_add_to_usergroups():
    user = UserAction(user="user@example.com")
    user.add_to_groups(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"add": {"group": ["Photoshop", "Illustrator"]}}],
                                "user": "user@example.com"}


def test_remove_from_products():
    user = UserAction(user="user@example.com")
    user.remove_from_groups(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"remove": {"group": ["Photoshop", "Illustrator"]}}],
                                "user": "user@example.com"}


def test_remove_from_groups_all():
    user = UserAction(user="user@example.com")
    user.remove_from_groups(all_groups=True)
    assert user.wire_dict() == {"do": [{"remove": "all"}],
                                "user": "user@example.com"}


def test_remove_from_groups_federatedid_all_error():
    user = UserAction(user="user@example.com")
    with pytest.raises(ValueError):
        user.remove_from_groups(all_groups=True, groups=['group1', 'group2'])


def test_remove_from_organization():
    user = UserAction(user="user@example.com")
    user.remove_from_organization()
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": False}}],
                                "user": "user@example.com"}


def test_remove_from_organization_adobeid():
    user = UserAction(user="user@example.com", use_adobe_id=True)
    user.remove_from_organization()
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": False}}],
                                "user": "user@example.com",
                                "useAdobeID": True}


def test_remove_from_organization_delete():
    user = UserAction(user="user@example.com")
    user.remove_from_organization(delete_account=True)
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": True}}],
                                "user": "user@example.com"}


def test_remove_from_organization_delete_adobeid():
    user = UserAction(user="user@example.com", use_adobe_id=True)
    user.remove_from_organization(delete_account=True)
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": True}}],
                                "user": "user@example.com",
                                "useAdobeID": True}

def test_add_to_products():
    group = GroupAction(group_name="SampleUsers")
    group.add_to_products(products=["Photoshop", "Illustrator"])
    assert group.wire_dict() == {"do": [{"add": {"productConfiguration": ["Photoshop", "Illustrator"]}}],
                                 "usergroup": "SampleUsers"}

def test_add_to_products_all():
    group = GroupAction(group_name="SampleUsers")
    group.add_to_products(all_products=True)
    assert group.wire_dict() == {"do": [{"add": "all"}],
                                 "usergroup": "SampleUsers"}


def test_add_to_products_all_error():
    group = GroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.add_to_products(all_products=True, products=["Photoshop"])


def test_remove_from_products():
    group = GroupAction(group_name="SampleUsers")
    group.remove_from_products(products=["Photoshop", "Illustrator"])
    assert group.wire_dict() == {"do": [{"remove": {"productConfiguration": ["Photoshop", "Illustrator"]}}],
                                 "usergroup": "SampleUsers"}


def test_remove_from_products_all():
    group = GroupAction(group_name="SampleUsers")
    group.remove_from_products(all_products=True)
    assert group.wire_dict() == {"do": [{"remove": "all"}],
                                 "usergroup": "SampleUsers"}


def test_remove_from_products_all_error():
    group = GroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.remove_from_products(all_products=True, products=["Photoshop"])


def test_add_users():
    group = GroupAction(group_name="SampleUsers")
    group.add_users(users=["user1@example.com", "user2@mydomain.net"])
    assert group.wire_dict() == {"do": [{"add": {"user": ["user1@example.com", "user2@mydomain.net"]}}],
                                 "usergroup": "SampleUsers"}


def test_add_users_error():
    group = GroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.add_users(users=[])


def test_remove_users():
    group = GroupAction(group_name="SampleUsers")
    group.remove_users(users=["user1@example.com", "user2@mydomain.net"])
    assert group.wire_dict() == {"do": [{"remove": {"user": ["user1@example.com", "user2@mydomain.net"]}}],
                                 "usergroup": "SampleUsers"}


def test_remove_users_error():
    group = GroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.remove_users(users=[])


def test_create_user_group():
    group = GroupAction(group_name="Test Group")
    group.create(description="Test Group Description")
    assert group.wire_dict() == {'do': [{'createUserGroup': {'option': 'ignoreIfAlreadyExists',
                                                             'description': 'Test Group Description'}}],
                                 'usergroup': 'Test Group'}


def test_create_user_group_error():
    group = GroupAction(group_name="Test Group")
    group.create(description="Test Group Description")
    with pytest.raises(ArgumentError):
        group.create()


def test_invalid_user_group_name():
    group = GroupAction(group_name="_Invalid Group Name")
    with pytest.raises(ArgumentError):
        group.create()
    with pytest.raises(ArgumentError):
        group.update(name="_Another invalid group name")


def test_long_user_group_name():
    long_group_name = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna 
    aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur 
    sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
    group = GroupAction(group_name=long_group_name)
    with pytest.raises(ArgumentError):
        group.create()
    with pytest.raises(ArgumentError):
        group.update(name=long_group_name)


def test_update_user_group():
    group = GroupAction(group_name="Test Group")
    group.update(name="Renamed Test Group", description="Test Group Description")
    assert group.wire_dict() == {'do': [{'updateUserGroup': {'name': 'Renamed Test Group',
                                                             'description': 'Test Group Description'}}],
                                 'usergroup': 'Test Group'}


def test_delete_user_group():
    group = GroupAction("Test Group")
    group.delete()
    assert group.wire_dict() == {'do': [{'deleteUserGroup': {}}],
                                 'usergroup': 'Test Group'}


def test_query_users(mock_connection_params):
    conn = Connection(**mock_connection_params)
    query = UsersQuery(conn)
    assert query.url_params == []
    assert query.query_params == {"directOnly": True}
    query = UsersQuery(conn, in_group="test", in_domain="test.com", direct_only=False)
    assert query.url_params == ["test"]
    assert query.query_params == {"directOnly": False, "domain": "test.com"}


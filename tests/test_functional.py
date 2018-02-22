# coding: utf-8

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

import pytest
import six
import mock

from conftest import mock_connection_params, MockResponse
from umapi_client import ArgumentError, RequestError
from umapi_client import Connection
from umapi_client import IdentityTypes, GroupTypes, RoleTypes
from umapi_client import UserAction, UserGroupAction
from umapi_client import UsersQuery


def test_user_emptyid():
    with pytest.raises(ValueError):
        UserAction(id_type=IdentityTypes.federatedID)


def test_user_adobeid():
    user = UserAction(email="dbrotsky@adobe.com")
    assert user.wire_dict() == {"do": [],
                                "user": "dbrotsky@adobe.com",
                                "useAdobeID": True}


def test_user_adobeid_unicode():
    user = UserAction(email=u"lwalesa@adobe.com")
    assert user.wire_dict() == {"do": [],
                                "user": u"lwalesa@adobe.com",
                                "useAdobeID": True}


def test_user_adobeid_unicode_error_unicode_dot_above():
    with pytest.raises(ValueError) as excinfo:
        UserAction(email=u"lwałęsa@adobe.com")
    assert excinfo.type == ArgumentError
    if six.PY2:
        assert excinfo.match(u"lwałęsa@adobe.com".encode('utf8'))
        with pytest.raises(ValueError) as excinfo:
            UserAction(email=u"lwałęsa@adobe.com".encode('utf8'))
        assert excinfo.type == ArgumentError
        assert excinfo.match(u"lwałęsa@adobe.com".encode('utf8'))


def test_user_adobeid_unicode_error_trailing_dot():
    with pytest.raises(ValueError):
        UserAction(email=u"lwalesa.@adobe.com")


def test_user_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky@o.on-the-side.net"}


def test_user_enterpriseid_username():
    with pytest.raises(ValueError):
        UserAction(id_type=IdentityTypes.enterpriseID, username="dbrotsky", domain="o.on-the-side.net")


def test_user_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky@k.on-the-side.net"}


def test_user_federatedid_username():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky", "domain": "k.on-the-side.net"}


def test_user_federatedid_username_unicode_error():
    with pytest.raises(ValueError):
        UserAction(id_type=IdentityTypes.federatedID, username=u"lwałęsa", domain="k.on-the-side.net")


def test_create_user_adobeid():
    user = UserAction(email="dbrotsky@adobe.com")
    user.create()
    assert user.wire_dict() == {"do": [{"addAdobeID": {"email": "dbrotsky@adobe.com",
                                                       "option": "ignoreIfAlreadyExists"}}],
                                "user": "dbrotsky@adobe.com",
                                "useAdobeID": True}


def test_create_user_adobeid_country():
    user = UserAction(email="dbrotsky@adobe.com")
    user.create(country="US")
    assert user.wire_dict() == {"do": [{"addAdobeID": {"email": "dbrotsky@adobe.com",
                                                       "country": "US",
                                                       "option": "ignoreIfAlreadyExists"}}],
                                "user": "dbrotsky@adobe.com",
                                "useAdobeID": True}


def test_create_user_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky")
    assert user.wire_dict() == {"do": [{"createEnterpriseID": {"email": "dbrotsky@o.on-the-side.net",
                                                               "firstname": "Daniel", "lastname": "Brotsky",
                                                               "option": "ignoreIfAlreadyExists"}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_create_user_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky", country="US")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "dbrotsky@k.on-the-side.net",
                                                              "firstname": "Daniel", "lastname": "Brotsky",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_create_user_federated_id_unicode():
    user = UserAction(id_type=IdentityTypes.federatedID, email=u"lwalesa@k.on-the-side.net")
    user.create(first_name="Lech", last_name=u"Wałęsa", country="PL")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": u"lwalesa@k.on-the-side.net",
                                                              "firstname": "Lech", "lastname": u"Wałęsa",
                                                              "country": "PL",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": u"lwalesa@k.on-the-side.net"}


def test_create_user_federatedid_username():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky", country="US", email="dbrotsky@k.on-the-side.net")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "dbrotsky@k.on-the-side.net",
                                                              "firstname": "Daniel", "lastname": "Brotsky",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "dbrotsky", "domain": "k.on-the-side.net"}


def test_create_user_federatedid_username_unicode():
    user = UserAction(id_type=IdentityTypes.federatedID, username=u"lwalesa", domain="k.on-the-side.net")
    user.create(first_name="Lech", last_name=u"Wałęsa", country="PL", email=u"lwalesa@k.on-the-side.net")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": u"lwalesa@k.on-the-side.net",
                                                              "firstname": "Lech", "lastname": u"Wałęsa",
                                                              "country": "PL",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": u"lwalesa", "domain": "k.on-the-side.net"}


def test_create_user_federatedid_username_email():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net",
                      email="dbrotsky@k.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky", country="US")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "dbrotsky@k.on-the-side.net",
                                                              "firstname": "Daniel", "lastname": "Brotsky",
                                                              "country": "US",
                                                              "option": "ignoreIfAlreadyExists"}}],
                                "user": "dbrotsky", "domain": "k.on-the-side.net"}


def test_create_user_federatedid_username_mismatch():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net",
                      email="foo@bar.net")
    with pytest.raises(ValueError):
        user.create(first_name="Daniel", last_name="Brotsky", country="US", email="foo@bar.com")


def test_update_user_adobeid():
    user = UserAction(id_type=IdentityTypes.adobeID, email="dbrotsky@adobe.com")
    user.update(first_name="Johnny", last_name="Danger")
    assert user.wire_dict() == {"do": [{"update": {"firstname": "Johnny", "lastname": "Danger"}}],
                                "user": "dbrotsky@adobe.com",
                                "useAdobeID": True}


def test_update_user_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.update(first_name="Johnny", last_name="Danger")
    assert user.wire_dict() == {"do": [{"update": {"firstname": "Johnny", "lastname": "Danger"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_update_user_federatedid_unicode():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.update(first_name=u"André", last_name="Danger")
    assert user.wire_dict() == {"do": [{"update": {"firstname": u"André", "lastname": "Danger"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_update_user_enterpriseid_username():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    with pytest.raises(ValueError):
        user.update(username="dbrotsky1@o.on-the-side.net")


def test_update_user_federatedid_username():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.update(username="dbrotsky1")
    assert user.wire_dict() == {"do": [{"update": {"username": "dbrotsky1"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_org_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_to_groups()
    assert user.wire_dict() == {"do": [{"add": {"product": []}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_products_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_to_groups(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"add": {"product": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_products_federatedid_unicode():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_to_groups(groups=["Photoshop", u"Người vẽ minh hoạ"])
    assert user.wire_dict() == {"do": [{"add": {"product": ["Photoshop", u"Người vẽ minh hoạ"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_to_groups_federatedid_all():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_to_groups(all_groups=True)
    assert user.wire_dict() == {"do": [{"add": "all"}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_to_groups_federatedid_all_error():
    user = UserAction(id_type="federatedID", email="dbrotsky@k.on-the-side.net")
    with pytest.raises(ValueError):
        user.add_to_groups(all_groups=True, groups=["Photoshop"])


def test_add_to_usergroups_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_to_groups(groups=["Photoshop", "Illustrator"], group_type=GroupTypes.usergroup)
    assert user.wire_dict() == {"do": [{"add": {"usergroup": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_to_usergroups_federatedid_unicode():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_to_groups(groups=["Photoshop", u"Người vẽ minh hoạ"], group_type=GroupTypes.usergroup)
    assert user.wire_dict() == {"do": [{"add": {"usergroup": ["Photoshop", u"Người vẽ minh hoạ"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_products_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_from_groups(groups=["Photoshop", "Illustrator"], group_type="product")
    assert user.wire_dict() == {"do": [{"remove": {"product": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_groups_federatedid_all():
    user = UserAction(id_type='federatedID', email="dbrotsky@k.on-the-side.net")
    user.remove_from_groups(all_groups=True)
    assert user.wire_dict() == {"do": [{"remove": "all"}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_groups_federatedid_all_error():
    user = UserAction(id_type='federatedID', email="dbrotsky@k.on-the-side.net")
    with pytest.raises(ValueError):
        user.remove_from_groups(all_groups=True, group_type="usergroup")


def test_add_role_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.add_role(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"addRoles": {"admin": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_add_role_enterpriseid_unicode():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.add_role(groups=[u"người quản lý"])
    assert user.wire_dict() == {"do": [{"addRoles": {"admin": [u"người quản lý"]}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_add_role_enterpriseid_error():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    with pytest.raises(ValueError):
        user.add_role(groups=[], role_type=RoleTypes.admin)


def test_remove_role_enterpriseid():
    user = UserAction(id_type='enterpriseID', email="dbrotsky@o.on-the-side.net")
    user.remove_role(groups=["Photoshop", "Illustrator"], role_type="productAdmin")
    assert user.wire_dict() == {"do": [{"removeRoles": {"productAdmin": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_remove_from_organization_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_from_organization()
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": False}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_organization_adobeid():
    user = UserAction(id_type='adobeID', email="dbrotsky@adobe.com")
    user.remove_from_organization()
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": False}}],
                                "user": "dbrotsky@adobe.com",
                                "useAdobeID": True}


def test_remove_from_organization_delete_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_from_organization(delete_account=True)
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": True}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_organization_delete_adobeid():
    user = UserAction(id_type=IdentityTypes.adobeID, email="dbrotsky@adobe.com")
    user.remove_from_organization(delete_account=True)
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"deleteAccount": True}}],
                                "user": "dbrotsky@adobe.com",
                                "useAdobeID": True}


def test_delete_account_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.delete_account()
    assert user.wire_dict() == {"do": [{"removeFromDomain": {}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_delete_account_adobeid():
    user = UserAction(id_type=IdentityTypes.adobeID, email="dbrotsky@adobe.com")
    with pytest.raises(ValueError):
        user.delete_account()


def test_add_to_products():
    group = UserGroupAction(group_name="SampleUsers")
    group.add_to_products(products=["Photoshop", "Illustrator"])
    assert group.wire_dict() == {"do": [{"add": {"productConfiguration": ["Photoshop", "Illustrator"]}}],
                                 "usergroup": "SampleUsers"}


def test_add_to_products_all():
    group = UserGroupAction(group_name="SampleUsers")
    group.add_to_products(all_products=True)
    assert group.wire_dict() == {"do": [{"add": "all"}],
                                 "usergroup": "SampleUsers"}


def test_add_to_products_all_error():
    group = UserGroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.add_to_products(all_products=True, products=["Photoshop"])


def test_remove_from_products():
    group = UserGroupAction(group_name="SampleUsers")
    group.remove_from_products(products=["Photoshop", "Illustrator"])
    assert group.wire_dict() == {"do": [{"remove": {"productConfiguration": ["Photoshop", "Illustrator"]}}],
                                 "usergroup": "SampleUsers"}


def test_remove_from_products_all():
    group = UserGroupAction(group_name="SampleUsers")
    group.remove_from_products(all_products=True)
    assert group.wire_dict() == {"do": [{"remove": "all"}],
                                 "usergroup": "SampleUsers"}


def test_remove_from_products_all_error():
    group = UserGroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.remove_from_products(all_products=True, products=["Photoshop"])


def test_add_users():
    group = UserGroupAction(group_name="SampleUsers")
    group.add_users(users=["user1@example.com", "user2@mydomain.net"])
    assert group.wire_dict() == {"do": [{"add": {"user": ["user1@example.com", "user2@mydomain.net"]}}],
                                 "usergroup": "SampleUsers"}


def test_add_users_unicode():
    group = UserGroupAction(group_name=u"người quản lý")
    group.add_users(users=[u"lwałęsa@adobe.com", u"tkolář@test1.on-the-side.net"])
    assert group.wire_dict() == {"do": [{"add": {"user": [u"lwałęsa@adobe.com", u"tkolář@test1.on-the-side.net"]}}],
                                 "usergroup": u"người quản lý"}


def test_add_users_error():
    group = UserGroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.add_users(users=[])


def test_remove_users():
    group = UserGroupAction(group_name="SampleUsers")
    group.remove_users(users=["user1@example.com", "user2@mydomain.net"])
    assert group.wire_dict() == {"do": [{"remove": {"user": ["user1@example.com", "user2@mydomain.net"]}}],
                                 "usergroup": "SampleUsers"}


def test_remove_users_error():
    group = UserGroupAction(group_name="SampleUsers")
    with pytest.raises(ValueError):
        group.remove_users(users=[])


def test_create_user_group():
    group = UserGroupAction(group_name="Test Group")
    group.create(description="Test Group Description")
    assert group.wire_dict() == {'do': [{'createUserGroup': {'option': 'ignoreIfAlreadyExists',
                                                             'description': 'Test Group Description'}}],
                                 'usergroup': 'Test Group'}


def test_create_user_group_error():
    group = UserGroupAction(group_name="Test Group")
    group.create(description="Test Group Description")
    with pytest.raises(ArgumentError):
        group.create()


def test_invalid_user_group_name():
    group = UserGroupAction(group_name="_Invalid Group Name")
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
    group = UserGroupAction(group_name=long_group_name)
    with pytest.raises(ArgumentError):
        group.create()
    with pytest.raises(ArgumentError):
        group.update(name=long_group_name)


def test_update_user_group():
    group = UserGroupAction(group_name="Test Group")
    group.update(name="Renamed Test Group", description="Test Group Description")
    assert group.wire_dict() == {'do': [{'updateUserGroup': {'name': 'Renamed Test Group',
                                                             'description': 'Test Group Description'}}],
                                 'usergroup': 'Test Group'}


def test_delete_user_group():
    group = UserGroupAction("Test Group")
    group.delete()
    assert group.wire_dict() == {'do': [{'deleteUserGroup': {}}],
                                 'usergroup': 'Test Group'}


def test_query_users():
    conn = Connection(**mock_connection_params)
    query = UsersQuery(conn)
    assert query.url_params == []
    assert query.query_params == {"directOnly": True}
    query = UsersQuery(conn, in_group="test", in_domain="test.com", direct_only=False)
    assert query.url_params == ["test"]
    assert query.query_params == {"directOnly": False, "domain": "test.com"}


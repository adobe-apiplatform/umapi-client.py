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

from umapi_client import IdentityTypes
from umapi_client import UserAction


def test_user_adobeid():
    user = UserAction(email="dbrotsky@adobe.com")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky@adobe.com"}


def test_user_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky@o.on-the-side.net"}


def test_user_enterpriseid_username():
    with pytest.raises(ValueError):
        user = UserAction(id_type=IdentityTypes.enterpriseID, username="dbrotsky", domain="o.on-the-side.net")


def test_user_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky@k.on-the-side.net"}


def test_user_federatedid_username():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net")
    assert user.wire_dict() == {"do": [], "user": "dbrotsky", "domain": "k.on-the-side.net"}


def test_create_user_adobeid():
    user = UserAction(email="dbrotsky@adobe.com")
    user.create()
    assert user.wire_dict() == {"do": [{"addAdobeID": {"email": "dbrotsky@adobe.com"}}],
                                "user": "dbrotsky@adobe.com"}


def test_create_user_adobeid_country():
    user = UserAction(email="dbrotsky@adobe.com")
    with pytest.raises(ValueError):
        user.create(country="US")


def test_create_user_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky")
    assert user.wire_dict() == {"do": [{"createEnterpriseID": {"email": "dbrotsky@o.on-the-side.net",
                                                               "firstName": "Daniel", "lastName": "Brotsky",
                                                               "country": "UD"}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_create_user_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky", country="US")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "dbrotsky@k.on-the-side.net",
                                                              "firstName": "Daniel", "lastName": "Brotsky",
                                                              "country": "US"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_create_user_federatedid_username():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net")
    user.create(first_name="Daniel", last_name="Brotsky", country="US", email="dbrotsky@k.on-the-side.net")
    assert user.wire_dict() == {"do": [{"createFederatedID": {"email": "dbrotsky@k.on-the-side.net",
                                                              "firstName": "Daniel", "lastName": "Brotsky",
                                                              "country": "US"}}],
                                "user": "dbrotsky", "domain": "k.on-the-side.net"}


def test_create_user_federatedid_username_mismatch():
    user = UserAction(id_type=IdentityTypes.federatedID, username="dbrotsky", domain="k.on-the-side.net")
    with pytest.raises(ValueError):
        user.create(first_name="Daniel", last_name="Brotsky", country="US", email="foo@bar.com")


def test_update_user_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.update(first_name="Johnny", last_name="Danger")
    assert user.wire_dict() == {"do": [{"update": {"firstName": "Johnny", "lastName": "Danger"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_update_user_enterpriseid_username():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    with pytest.raises(ValueError):
        user.update(username="dbrotsky1")


def test_update_user_federatedid_username():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.update(username="dbrotsky1")
    assert user.wire_dict() == {"do": [{"update": {"username": "dbrotsky1"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_product_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.add_group(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"add": {"product": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_product_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_group(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"remove": {"product": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_product_federatedid_all():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_group(all_groups=True)
    assert user.wire_dict() == {"do": [{"remove": "all"}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_add_role_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.add_role(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"addRoles": {"admin": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_remove_role_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.remove_role(groups=["Photoshop", "Illustrator"])
    assert user.wire_dict() == {"do": [{"removeRoles": {"admin": ["Photoshop", "Illustrator"]}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_remove_from_organization_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_from_organization()
    assert user.wire_dict() == {"do": [{"removeFromOrg": {}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_organization_adobeid():
    user = UserAction(id_type=IdentityTypes.adobeID, email="dbrotsky@adobe.com")
    user.remove_from_organization()
    assert user.wire_dict() == {"do": [{"removeFromOrg": {}}],
                                "user": "dbrotsky@adobe.com"}


def test_remove_from_organization_delete_federatedid():
    user = UserAction(id_type=IdentityTypes.federatedID, email="dbrotsky@k.on-the-side.net")
    user.remove_from_organization(delete_account=True)
    assert user.wire_dict() == {"do": [{"removeFromOrg": {"removedDomain": "k.on-the-side.net"}}],
                                "user": "dbrotsky@k.on-the-side.net"}


def test_remove_from_organization_delete_adobeid():
    user = UserAction(id_type=IdentityTypes.adobeID, email="dbrotsky@adobe.com")
    with pytest.raises(ValueError):
        user.remove_from_organization(delete_account=True)


def test_delete_account_enterpriseid():
    user = UserAction(id_type=IdentityTypes.enterpriseID, email="dbrotsky@o.on-the-side.net")
    user.delete_account()
    assert user.wire_dict() == {"do": [{"removeFromDomain": {"domain": "o.on-the-side.net"}}],
                                "user": "dbrotsky@o.on-the-side.net"}


def test_delete_account_adobeid():
    user = UserAction(id_type=IdentityTypes.adobeID, email="dbrotsky@adobe.com")
    with pytest.raises(ValueError):
        user.delete_account()

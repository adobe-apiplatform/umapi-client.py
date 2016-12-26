# Copyright (c) 2016 Adobe Systems Incorporated.  All rights reserved.
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

import mock
import json
import pytest

from conftest import MockResponse
from umapi_client.legacy import UMAPI, Action
from umapi_client.legacy import UMAPIError, UMAPIRetryError, UMAPIRequestError, ActionFormatError


# These values will be returned in the various cases by get/post
success_response = MockResponse(200, {"result": "success"})
error_response = MockResponse(200, {"result": "error", "errors": [{"errorCode": "test.error"}]})
retry_response = MockResponse(429, headers={"Retry-After": "1"})
not_found_response = MockResponse(404, text="404 Object Not Found")
                
@mock.patch('umapi_client.legacy.requests.get', return_value=success_response)
def test_list_users_success(_):
    """Test Users List - SUCCESS"""
    api = UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)
    assert api.users(None) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.get', return_value=error_response)
def test_list_users_error(_):
    """Test Users List - ERROR"""
    api = UMAPI('http://example.com/error', "N/A", retry_max_attempts=1)
    pytest.raises(UMAPIRequestError, api.users, None)


@mock.patch('umapi_client.legacy.requests.get', return_value=not_found_response)
def test_list_users_failure(patch):
    """Test Users List - FAILURE"""
    api = UMAPI('http://example.com/failure', "N/A", retry_max_attempts=1)
    pytest.raises(UMAPIError, api.users, None)
    patch.return_value = retry_response
    api = UMAPI('http://example.com/retry', "N/A", retry_max_attempts=1)
    pytest.raises(UMAPIRetryError, api.users, None)


@mock.patch('umapi_client.legacy.requests.get', return_value=success_response)
def test_list_groups_success(_):
    """Test Groups List - SUCCESS"""
    api = UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)
    assert api.groups(None) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.post', return_value=success_response)
def test_user_create_success(_):
    """Test User Creation - SUCCESS"""
    api = UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)

    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )

    assert api.action(None, action) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.post', return_value=error_response)
def test_user_create_error(_):
    """Test User Creation - ERROR"""
    api = UMAPI('http://example.com/error', "N/A", retry_max_attempts=1)

    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    pytest.raises(UMAPIRequestError, api.action, None, action)


@mock.patch('umapi_client.legacy.requests.post', return_value=not_found_response)
def test_user_create_failure(patch):
    """Test User Creation - FAILURE"""
    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    api = UMAPI('http://example.com/failure', "N/A", retry_max_attempts=1)
    pytest.raises(UMAPIError, api.action, None, action)
    patch.return_value = retry_response
    api = UMAPI('http://example.com/retry', "N/A", retry_max_attempts=1)
    pytest.raises(UMAPIRetryError, api.action, None, action)


@mock.patch('umapi_client.legacy.requests.post', return_value=success_response)
def test_product_add(_):
    """Test Product Add - SUCCESS"""
    api = UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)

    action = Action(user_key="user@example.com").do(
        add=["product1", "product2"]
    )

    assert api.action(None, action) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.post', return_value=success_response)
def test_action_format_error(_):
    """Test Action Format Error"""
    api = UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)
    action = ''
    pytest.raises(ActionFormatError, api.action, None, action)


def test_action_obj_create():
    """"Create a user creation action object and make sure that we can serialize it in the expected format"""
    action = Action(user="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'
    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'


def test_action_obj_remove():
    """"Create a user removal action object"""
    action = Action(user="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'
    action = Action(user_key="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'


def test_action_obj_update():
    """Create a user update action object"""
    action = Action(user="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"update": {"firstname": "example", "lastname": "user"}}], "user": "user@example.com"}'
    action = Action(user_key="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"update": {"firstname": "example", "lastname": "user"}}], "user": "user@example.com"}'


def test_action_obj_multi():
    """Create a multi-action action object"""
    action = Action(user="user@example.com").do(
        addAdobeID={"email": "user@example.com"},
        add=["product1", "product2"],
        remove=["product3"]
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}, {"add": {"product": ["product1", "product2"]}}, {"remove": {"product": ["product3"]}}], "user": "user@example.com"}'


def test_action_obj_requestid():
    """Include a request ID in action object"""
    action = Action(user="user@example.com", requestID="abc123").do(
        add=["product1"]
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"add": {"product": ["product1"]}}], "requestID": "abc123", "user": "user@example.com"}'

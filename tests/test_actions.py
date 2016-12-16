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

from umapi_client import UMAPI, Action
from umapi_client.error import UMAPIError, UMAPIRetryError, UMAPIRequestError, ActionFormatError
from umapi_client.auth import Auth


# This method will be used by the mock to replace requests.get / requests.post
def mocked_requests_call(target, **kwargs):
    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self.data = data

        def json(self):
            return self.data

    if 'http://example.com/success' in target:
        return MockResponse(200, {"result": "success"})
    elif 'http://example.com/error' in target:
        return MockResponse(200, {"result": "error", "errors": [{"errorCode": "test.error"}]})
    elif 'http://example.com/retry' in target:
        return MockResponse(429, {})
    else:
        return MockResponse(404, {})


@mock.patch('umapi_client.api.requests.get', side_effect=mocked_requests_call)
def test_list_users_success(_):
    """Test Users List - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    assert api.users(None) == {"result": "success"}


@mock.patch('umapi_client.api.requests.get', side_effect=mocked_requests_call)
def test_list_users_error(_):
    """Test Users List - ERROR"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/error', auth)
    pytest.raises(UMAPIRequestError, api.users, None)


@mock.patch('umapi_client.api.requests.get', side_effect=mocked_requests_call)
def test_list_users_failure(_):
    """Test Users List - FAILURE"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/failure', auth)
    pytest.raises(UMAPIError, api.users, None)
    api = UMAPI('http://example.com/retry', auth)
    pytest.raises(UMAPIRetryError, api.users, None)


@mock.patch('umapi_client.api.requests.get', side_effect=mocked_requests_call)
def test_list_groups_success(_):
    """Test Groups List - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    assert api.groups(None) == {"result": "success"}


@mock.patch('umapi_client.api.requests.post', side_effect=mocked_requests_call)
def test_user_create_success(_):
    """Test User Creation - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)

    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )

    assert api.action(None, action) == {"result": "success"}


@mock.patch('umapi_client.api.requests.post', side_effect=mocked_requests_call)
def test_user_create_error(_):
    """Test User Creation - ERROR"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/error', auth)

    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    pytest.raises(UMAPIRequestError, api.action, None, action)


@mock.patch('umapi_client.api.requests.post', side_effect=mocked_requests_call)
def test_user_create_failure(_):
    """Test User Creation - FAILURE"""
    auth = mock.create_autospec(Auth)

    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )

    api = UMAPI('http://example.com/failure', auth)
    pytest.raises(UMAPIError, api.action, None, action)
    api = UMAPI('http://example.com/retry', auth)
    pytest.raises(UMAPIRetryError, api.action, None, action)


@mock.patch('umapi_client.api.requests.post', side_effect=mocked_requests_call)
def test_product_add(_):
    """Test Product Add - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)

    action = Action(user_key="user@example.com").do(
        add=["product1", "product2"]
    )

    assert api.action(None, action) == {"result": "success"}


@mock.patch('umapi_client.api.requests.post', side_effect=mocked_requests_call)
def test_action_format_error(_):
    """Test Action Format Error"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    action = ''
    pytest.raises(ActionFormatError, api.action, None, action)


def test_action_obj_create():
    """"Create a user creation action object and make sure that we can serialize it in the expected format"""
    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.data, sort_keys=True) ==\
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'


def test_action_obj_remove():
    """"Create a user removal action object"""
    action = Action(user_key="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.data, sort_keys=True) ==\
           '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'


def test_action_obj_update():
    """Create a user update action object"""
    action = Action(user_key="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.data, sort_keys=True) ==\
           '{"do": [{"update": {"firstname": "example", "lastname": "user"}}], "user": "user@example.com"}'


def test_action_obj_multi():
    """Create a multi-action action object"""
    action = Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"},
        add=["product1", "product2"],
        remove=["product3"]
    )
    assert json.dumps(action.data, sort_keys=True) ==\
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}, {"add": {"product": ["product1", "product2"]}}, {"remove": {"product": ["product3"]}}], "user": "user@example.com"}'


def test_action_obj_requestid():
    """Include a request ID in action object"""
    action = Action(user_key="user@example.com", requestID="abc123").do(
        add=["product1"]
    )
    assert json.dumps(action.data, sort_keys=True) ==\
           '{"do": [{"add": {"product": ["product1"]}}], "requestID": "abc123", "user": "user@example.com"}'

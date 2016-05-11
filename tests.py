import mock
import json
from umapi import UMAPI, Action
from umapi.error import UMAPIError, UMAPIRetryError
from umapi.auth import Auth
from nose.tools import *


# This method will be used by the mock to replace requests.get
def mocked_requests_call(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self.data = data

        def json(self):
            return json.dumps(self.data)

    if 'http://example.com/success' in args[0]:
        return MockResponse(200, {"result": "success"})
    elif 'http://example.com/error' in args[0]:
        return MockResponse(200, {"result": "error"})
    elif 'http://example.com/retry' in args[0]:
        return MockResponse(429, {})
    else:
        return MockResponse(404, {})


@mock.patch('umapi.api.requests.get', side_effect=mocked_requests_call)
def test_list_users_success(mock_requests):
    """Test Users List - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    assert api.users(None) == '{"result": "success"}'


@mock.patch('umapi.api.requests.get', side_effect=mocked_requests_call)
def test_list_users_error(mock_requests):
    """Test Users List - ERROR"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/error', auth)
    assert api.users(None) == '{"result": "error"}'


@mock.patch('umapi.api.requests.get', side_effect=mocked_requests_call)
def test_list_users_failure(mock_requests):
    """Test Users List - FAILURE"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/failure', auth)
    assert_raises(UMAPIError, api.users, None)
    api = UMAPI('http://example.com/retry', auth)
    assert_raises(UMAPIRetryError, api.users, None)


@mock.patch('umapi.api.requests.get', side_effect=mocked_requests_call)
def test_list_groups_success(mock_requests):
    """Test Groups List - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    assert api.groups(None) == '{"result": "success"}'


@mock.patch('umapi.api.requests.post', side_effect=mocked_requests_call)
def test_user_create_success(mock_requests):
    """Test User Creation - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)

    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"}
    )

    assert api.action(None, action) == '{"result": "success"}'


@mock.patch('umapi.api.requests.post', side_effect=mocked_requests_call)
def test_user_create_error(mock_requests):
    """Test User Creation - ERROR"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/error', auth)

    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"}
    )

    assert api.action(None, action) == '{"result": "error"}'


@mock.patch('umapi.api.requests.post', side_effect=mocked_requests_call)
def test_user_create_success(mock_requests):
    """Test User Creation - FAILURE"""
    auth = mock.create_autospec(Auth)

    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"}
    )

    api = UMAPI('http://example.com/failure', auth)
    assert_raises(UMAPIError, api.action, None, action)
    api = UMAPI('http://example.com/retry', auth)
    assert_raises(UMAPIRetryError, api.action, None, action)


@mock.patch('umapi.api.requests.post', side_effect=mocked_requests_call)
def test_product_add(mock_requests):
    """Test Product Add - SUCCESS"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)

    action = Action(user="user@example.com").do(
        add=["product1", "product2"]
    )

    assert api.action(None, action) == '{"result": "success"}'


def test_action_obj_create():
    """"Create a user creation action object and make sure that we can serialize it in the expected format"""
    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.data) == '{"do": [{"createAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'


def test_action_obj_remove():
    """"Create a user removal action object"""
    action = Action(user="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.data) == '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'


def test_action_obj_update():
    """Create a user update action object"""
    action = Action(user="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.data) == '{"do": [{"update": {"lastname": "user", "firstname": "example"}}], "user": "user@example.com"}'


def test_action_obj_multi():
    """Create a multi-action action object"""
    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"},
        add=["product1", "product2"],
        remove=["product3"]
    )
    assert json.dumps(action.data) == '{"do": [{"createAdobeID": {"email": "user@example.com"}}, {"add": {"product": ["product1", "product2"]}}, {"remove": {"product": ["product3"]}}], "user": "user@example.com"}'

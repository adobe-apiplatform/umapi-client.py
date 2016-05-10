import mock
import json
from umapi import UMAPI, Action
from umapi.error import UMAPIError, UMAPIRetryError
from umapi.auth import Auth
from nose.tools import *


# This method will be used by the mock to replace requests.get
def mocked_requests_call(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

        def json(self):
            return '{}'

    if 'http://example.com/success' in args[0]:
        return MockResponse(200)
    elif 'http://example.com/retry' in args[0]:
        return MockResponse(429)
    else:
        return MockResponse(404)


@mock.patch('umapi.api.requests.get', side_effect=mocked_requests_call)
def test_list_users(mock_requests):
    """Goal of this test is to ensure that we are working with the requests
        library and handling errors appropriately"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    assert api.users(None) == '{}'
    api = UMAPI('http://example.com/failure', auth)
    assert_raises(UMAPIError, api.users, None)
    api = UMAPI('http://example.com/retry', auth)
    assert_raises(UMAPIRetryError, api.users, None)


@mock.patch('umapi.api.requests.get', side_effect=mocked_requests_call)
def test_list_groups(mock_requests):
    """Goal of this test is to ensure that we are working with the requests
        library and handling errors appropriately"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)
    assert api.groups(None) == '{}'


@mock.patch('umapi.api.requests.post', side_effect=mocked_requests_call)
def test_user_create(mock_requests):
    """Test User Creation"""
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)

    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"}
    )

    assert api.action(None, action) == '{}'

    api = UMAPI('http://example.com/failure', auth)
    assert_raises(UMAPIError, api.action, None, action)
    api = UMAPI('http://example.com/retry', auth)
    assert_raises(UMAPIRetryError, api.action, None, action)


@mock.patch('umapi.api.requests.post', side_effect=mocked_requests_call)
def test_product_add(mock_requests):
    auth = mock.create_autospec(Auth)
    api = UMAPI('http://example.com/success', auth)

    action = Action(user="user@example.com").do(
        add=["product1", "product2"]
    )

    assert api.action(None, action) == '{}'


def test_action_obj_create():
    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.data) == '{"do": [{"createAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'


def test_action_obj_remove():
    action = Action(user="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.data) == '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'


def test_action_obj_update():
    action = Action(user="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.data) == '{"do": [{"update": {"lastname": "user", "firstname": "example"}}], "user": "user@example.com"}'


def test_action_obj_multi():
    action = Action(user="user@example.com").do(
        createAdobeID={"email": "user@example.com"},
        add=["product1", "product2"],
        remove=["product3"]
    )
    assert json.dumps(action.data) == '{"do": [{"createAdobeID": {"email": "user@example.com"}}, {"add": {"product": ["product1", "product2"]}}, {"remove": {"product": ["product3"]}}], "user": "user@example.com"}'

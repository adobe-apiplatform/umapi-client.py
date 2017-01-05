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

import json
import logging
import time
from email.utils import formatdate

import mock
import pytest
from conftest import MockResponse
from six import StringIO

import umapi_client.legacy as v1

# These values will be returned in the various cases by get/post
success_response = MockResponse(200, {"result": "success"})
error_response = MockResponse(200, {"result": "error", "errors": [{"errorCode": "test.error"}]})
retry_response = MockResponse(429, headers={"Retry-After": "1"})
not_found_response = MockResponse(404, text="404 Object Not Found")
                
@mock.patch('umapi_client.legacy.requests.get', return_value=success_response)
def test_list_users_success(_):
    """Test Users List - SUCCESS"""
    api = v1.UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)
    assert api.users(None) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.get', return_value=error_response)
def test_list_users_error(_):
    """Test Users List - ERROR"""
    api = v1.UMAPI('http://example.com/error', "N/A", retry_max_attempts=1)
    pytest.raises(v1.UMAPIRequestError, api.users, None)


@mock.patch('umapi_client.legacy.requests.get', return_value=not_found_response)
def test_list_users_failure(patch):
    """Test Users List - FAILURE"""
    api = v1.UMAPI('http://example.com/failure', "N/A", retry_max_attempts=1)
    pytest.raises(v1.UMAPIError, api.users, None)
    patch.return_value = retry_response
    api = v1.UMAPI('http://example.com/retry', "N/A", retry_max_attempts=1)
    pytest.raises(v1.UMAPIRetryError, api.users, None)


@mock.patch('umapi_client.legacy.requests.get', return_value=success_response)
def test_list_groups_success(_):
    """Test Groups List - SUCCESS"""
    api = v1.UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)
    assert api.groups(None) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.post', return_value=success_response)
def test_user_create_success(_):
    """Test User Creation - SUCCESS"""
    api = v1.UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)

    action = v1.Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )

    assert api.action(None, action) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.post', return_value=error_response)
def test_user_create_error(_):
    """Test User Creation - ERROR"""
    api = v1.UMAPI('http://example.com/error', "N/A", retry_max_attempts=1)

    action = v1.Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    pytest.raises(v1.UMAPIRequestError, api.action, None, action)


@mock.patch('umapi_client.legacy.requests.post', return_value=not_found_response)
def test_user_create_failure(patch):
    """Test User Creation - FAILURE"""
    action = v1.Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    api = v1.UMAPI('http://example.com/failure', "N/A", retry_max_attempts=1)
    pytest.raises(v1.UMAPIError, api.action, None, action)
    patch.return_value = retry_response
    api = v1.UMAPI('http://example.com/retry', "N/A", retry_max_attempts=1)
    pytest.raises(v1.UMAPIRetryError, api.action, None, action)


@mock.patch('umapi_client.legacy.requests.post', return_value=success_response)
def test_product_add(_):
    """Test Product Add - SUCCESS"""
    api = v1.UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)

    action = v1.Action(user_key="user@example.com").do(
        add=["product1", "product2"]
    )

    assert api.action(None, action) == {"result": "success"}


@mock.patch('umapi_client.legacy.requests.post', return_value=success_response)
def test_action_format_error(_):
    """Test v1.Action Format Error"""
    api = v1.UMAPI('http://example.com/success', "N/A", retry_max_attempts=1)
    action = ''
    pytest.raises(v1.ActionFormatError, api.action, None, action)


def test_action_obj_create():
    """"Create a user creation action object and make sure that we can serialize it in the expected format"""
    action = v1.Action(user="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'
    action = v1.Action(user_key="user@example.com").do(
        addAdobeID={"email": "user@example.com"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}], "user": "user@example.com"}'


def test_action_obj_remove():
    """"Create a user removal action object"""
    action = v1.Action(user="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'
    action = v1.Action(user_key="user@example.com").do(
        removeFromOrg={}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"removeFromOrg": {}}], "user": "user@example.com"}'


def test_action_obj_update():
    """Create a user update action object"""
    action = v1.Action(user="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"update": {"firstname": "example", "lastname": "user"}}], "user": "user@example.com"}'
    action = v1.Action(user_key="user@example.com").do(
        update={"firstname": "example", "lastname": "user"}
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"update": {"firstname": "example", "lastname": "user"}}], "user": "user@example.com"}'


def test_action_obj_multi():
    """Create a multi-action action object"""
    action = v1.Action(user="user@example.com").do(
        addAdobeID={"email": "user@example.com"},
        add=["product1", "product2"],
        remove=["product3"]
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"addAdobeID": {"email": "user@example.com"}}, {"add": {"product": ["product1", "product2"]}}, {"remove": {"product": ["product3"]}}], "user": "user@example.com"}'


def test_action_obj_requestid():
    """Include a request ID in action object"""
    action = v1.Action(user="user@example.com", requestID="abc123").do(
        add=["product1"]
    )
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"add": {"product": ["product1"]}}], "requestID": "abc123", "user": "user@example.com"}'


#
# pageinate tests
#

# This method will be used by the mock to replace v1.UMAPI.users
def mocked_users(org_id, page):
    class ErrorResponse:
        def __init__(self, status_code, headers):
            self.status_code = status_code
            self.data = {}
            self.headers = headers
            self.text = "Error"

    if 'success' in org_id or page > 0:
        # return 3 pages, one value per page
        if page < 2:
            return {"result": "success", "users": ["user" + str(page)]}
        else:
            return {"result": "success", "users": ["user" + str(page)], "lastPage": True}
    elif 'retrySecs' in org_id:
        raise v1.UMAPIRetryError(ErrorResponse(429, {"Retry-After": "3"}))
    elif 'retryTime' in org_id:
        raise v1.UMAPIRetryError(ErrorResponse(502, {"Retry-After": formatdate(time.time() + 3.0)}))
    elif 'retryNone' in org_id:
        raise v1.UMAPIRetryError(ErrorResponse(503, {"Retry-After": "0"}))
    elif 'retryNull' in org_id:
        raise v1.UMAPIRetryError(ErrorResponse(504, {}))
    else:
        raise v1.UMAPIError(ErrorResponse(404, {}))


# test the pagination on success
@mock.patch('umapi_client.legacy.UMAPI.users', side_effect=mocked_users)
def test_helper_success(_):
    api = v1.UMAPI('', None)
    assert v1.paginate(api.users, 'success') == ["user0", "user1", "user2"]


@pytest.fixture
def reduce_attempts():
    # reduce the number of retry attempts
    v1.retry_max_attempts = 3


# test the retry logic with seconds in the header
@mock.patch('umapi_client.legacy.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_seconds(_, reduce_attempts):
    api = v1.UMAPI('', None)
    assert v1.paginate(api.users, 'retrySecs') == ["user1", "user2"]


# test the retry logic with a time in the header
@mock.patch('umapi_client.legacy.UMAPI.users', side_effect=mocked_users)
def test_helper_fail_date(_, reduce_attempts):
    api = v1.UMAPI('', None)
    assert v1.paginate(api.users, 'retryTime') == ["user1", "user2"]


# the default retry waits are really long, so don't use them while testing
@pytest.fixture
def reduce_delay():
    # reduce the wait on retry attempts
    v1.retry_max_attempts = 3
    v1.retry_exponential_backoff_factor = 1
    v1.retry_random_delay_max = 3


# test the retry logic with a zero delay in the header
@mock.patch('umapi_client.legacy.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_zero(_, reduce_delay, reduce_attempts):
    api = v1.UMAPI('', None)
    assert v1.paginate(api.users, 'retryNone') == ["user1", "user2"]


# test the retry logic with no header
@mock.patch('umapi_client.legacy.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_noheader(_, reduce_delay, reduce_attempts):
    api = v1.UMAPI('', None)
    assert v1.paginate(api.users, 'retryNull') == ["user1", "user2"]


# py.test doesn't divert string logging, so use it
@pytest.fixture
def log_stream():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    prior_logger = v1.logger
    v1.logger = logger
    yield stream
    v1.logger = prior_logger
    handler.close()


# test the retry logic with a custom logger
@mock.patch('umapi_client.legacy.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_logging(_, log_stream, reduce_attempts):
    api = v1.UMAPI('', None)
    assert v1.paginate(api.users, 'retrySecs') == ["user1", "user2"]
    log_stream.flush()
    log = log_stream.getvalue()  # save as a local so can do pytest -l to see exact log
    assert log == '''UMAPI service temporarily unavailable (attempt 1) -- 429
Next retry in 3 seconds...
UMAPI service temporarily unavailable (attempt 2) -- 429
Next retry in 3 seconds...
UMAPI service temporarily unavailable (attempt 3) -- 429
Next retry in 3 seconds...
UMAPI timeout...giving up on results page 0 after 3 attempts.
'''

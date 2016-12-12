import StringIO
import time
from email.utils import formatdate

import logging
import mock
import pytest

import adobe_umapi.helper
from adobe_umapi import UMAPI
from adobe_umapi.error import UMAPIError, UMAPIRetryError


# This method will be used by the mock to replace UMAPI.users
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
        raise UMAPIRetryError(ErrorResponse(429, {"Retry-After": "3"}))
    elif 'retryTime' in org_id:
        raise UMAPIRetryError(ErrorResponse(502, {"Retry-After": formatdate(time.time() + 3.0)}))
    elif 'retryNone' in org_id:
        raise UMAPIRetryError(ErrorResponse(503, {"Retry-After": "0"}))
    elif 'retryNull' in org_id:
        raise UMAPIRetryError(ErrorResponse(504, {}))
    else:
        raise UMAPIError(ErrorResponse(404, {}))

# test the pagination on success
@mock.patch('adobe_umapi.UMAPI.users', side_effect=mocked_users)
def test_helper_success(_mock):
    api = UMAPI('', None)
    assert adobe_umapi.helper.paginate(api.users, 'success') == ["user0", "user1", "user2"]

# test the retry logic with seconds in the header
@mock.patch('adobe_umapi.UMAPI.users', side_effect=mocked_users)
def test_helper_failSecs(_mock):
    api = UMAPI('', None)
    assert adobe_umapi.helper.paginate(api.users, 'retrySecs') == ["user1", "user2"]

# test the retry logic with a time in the header
@mock.patch('adobe_umapi.UMAPI.users', side_effect=mocked_users)
def test_helper_failTime(_mock):
    api = UMAPI('', None)
    assert adobe_umapi.helper.paginate(api.users, 'retryTime') == ["user1", "user2"]

# the default retry waits are really long, so don't use them while testing
@pytest.fixture
def reduce_delay():
    # reduce the wait on retry attempts
    adobe_umapi.helper.retry_max_attempts = 3
    adobe_umapi.helper.retry_exponential_backoff_factor = 1
    adobe_umapi.helper.retry_random_delay_max = 3

# test the retry logic with a zero delay in the header
@mock.patch('adobe_umapi.UMAPI.users', side_effect=mocked_users)
def test_helper_failNone(_mock, reduce_delay):
    api = UMAPI('', None)
    assert adobe_umapi.helper.paginate(api.users, 'retryNone') == ["user1", "user2"]

# test the retry logic with no header
@mock.patch('adobe_umapi.UMAPI.users', side_effect=mocked_users)
def test_helper_failNull(_mock, reduce_delay):
    api = UMAPI('', None)
    assert adobe_umapi.helper.paginate(api.users, 'retryNull') == ["user1", "user2"]

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

import logging
import time
from email.utils import formatdate

import mock
import pytest
from six import StringIO

import adobe_umapi_client.helper
from adobe_umapi_client import UMAPI
from adobe_umapi_client.error import UMAPIError, UMAPIRetryError


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
@mock.patch('adobe_umapi_client.UMAPI.users', side_effect=mocked_users)
def test_helper_success(_):
    api = UMAPI('', None)
    assert adobe_umapi_client.helper.paginate(api.users, 'success') == ["user0", "user1", "user2"]


@pytest.fixture
def reduce_attempts():
    # reduce the number of retry attempts
    adobe_umapi_client.helper.retry_max_attempts = 3


# test the retry logic with seconds in the header
@mock.patch('adobe_umapi_client.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_seconds(_, reduce_attempts):
    api = UMAPI('', None)
    assert adobe_umapi_client.helper.paginate(api.users, 'retrySecs') == ["user1", "user2"]


# test the retry logic with a time in the header
@mock.patch('adobe_umapi_client.UMAPI.users', side_effect=mocked_users)
def test_helper_fail_date(_, reduce_attempts):
    api = UMAPI('', None)
    assert adobe_umapi_client.helper.paginate(api.users, 'retryTime') == ["user1", "user2"]


# the default retry waits are really long, so don't use them while testing
@pytest.fixture
def reduce_delay():
    # reduce the wait on retry attempts
    adobe_umapi_client.helper.retry_max_attempts = 3
    adobe_umapi_client.helper.retry_exponential_backoff_factor = 1
    adobe_umapi_client.helper.retry_random_delay_max = 3


# test the retry logic with a zero delay in the header
@mock.patch('adobe_umapi_client.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_zero(_, reduce_delay, reduce_attempts):
    api = UMAPI('', None)
    assert adobe_umapi_client.helper.paginate(api.users, 'retryNone') == ["user1", "user2"]


# test the retry logic with no header
@mock.patch('adobe_umapi_client.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_noheader(_, reduce_delay, reduce_attempts):
    api = UMAPI('', None)
    assert adobe_umapi_client.helper.paginate(api.users, 'retryNull') == ["user1", "user2"]


# py.test doesn't divert string logging, so use it
@pytest.fixture
def log_stream():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    prior_logger = adobe_umapi_client.helper.logger
    adobe_umapi_client.helper.logger = logger
    yield stream
    adobe_umapi_client.helper.logger = prior_logger
    handler.close()


# test the retry logic with a custom logger
@mock.patch('adobe_umapi_client.UMAPI.users', side_effect=mocked_users)
def test_helper_retry_logging(_, log_stream, reduce_attempts):
    api = UMAPI('', None)
    assert adobe_umapi_client.helper.paginate(api.users, 'retrySecs') == ["user1", "user2"]
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

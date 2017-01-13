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

import time
from email.utils import formatdate

import mock
import pytest
import requests

from conftest import mock_connection_params, MockResponse
from umapi_client import Connection, UnavailableError, ServerError, RequestError


def test_remote_status_success():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(200, body={"build": "2559", "version": "2.1.54", "state":"LIVE"})
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status == {"endpoint": "https://test/", "build": "2559", "version": "2.1.54", "state":"LIVE"}


def test_remote_status_failure():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Not Found")
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status["status"].startswith("Unexpected")


def test_remote_status_timeout():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.side_effect = requests.Timeout
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status["status"].startswith("Unreachable")


def test_get_success():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])
        conn = Connection(**mock_connection_params)
        assert conn.make_call("").json() == ["test", "body"]


def test_post_success():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, body=["test", "body"])
        conn = Connection(**mock_connection_params)
        assert conn.make_call("", [3, 5]).json() == ["test", "body"]


def test_get_timeout():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.side_effect = requests.Timeout
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_timeout():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.side_effect = requests.Timeout
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "", [3, 5])


def test_get_retry_header_1():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(429, headers={"Retry-After": "1"})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_header_1():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(429, headers={"Retry-After": "1"})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


def test_get_retry_header_time_2():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(502, headers={"Retry-After": formatdate(time.time() + 2.5)})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_header_time_2():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(502, headers={"Retry-After": formatdate(time.time() + 2.5)})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


def test_get_retry_header_0():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(503, headers={"Retry-After": "0"})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_header_0():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(503, headers={"Retry-After": "0"})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


def test_get_retry_no_header():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(504)
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_no_header():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(504)
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


# log_stream fixture defined in conftest.py
def test_get_retry_logging(log_stream):
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(429, headers={"Retry-After": "3"})
        stream, logger = log_stream
        params = dict(mock_connection_params)
        params["logger"] = logger
        conn = Connection(**params)
        pytest.raises(UnavailableError, conn.make_call, "")
        stream.flush()
        log = stream.getvalue()  # save as a local so can do pytest -l to see exact log
        assert log == """UMAPI timeout...service unavailable (code 429 on try 1)
Next retry in 3 seconds...
UMAPI timeout...service unavailable (code 429 on try 2)
Next retry in 3 seconds...
UMAPI timeout...service unavailable (code 429 on try 3)
Next retry in 3 seconds...
UMAPI timeout...giving up after 3 attempts.
"""


# log_stream fixture defined in conftest.py
def test_post_retry_logging(log_stream):
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(429, headers={"Retry-After": "3"})
        stream, logger = log_stream
        params = dict(mock_connection_params)
        params["logger"] = logger
        conn = Connection(**params)
        pytest.raises(UnavailableError, conn.make_call, "", [3, 5])
        stream.flush()
        log = stream.getvalue()  # save as a local so can do pytest -l to see exact log
        assert log == """UMAPI timeout...service unavailable (code 429 on try 1)
Next retry in 3 seconds...
UMAPI timeout...service unavailable (code 429 on try 2)
Next retry in 3 seconds...
UMAPI timeout...service unavailable (code 429 on try 3)
Next retry in 3 seconds...
UMAPI timeout...giving up after 3 attempts.
"""


def test_get_server_fail():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(500, text="500 test server failure")
        conn = Connection(**mock_connection_params)
        pytest.raises(ServerError, conn.make_call, "")


def test_post_server_fail():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(500, text="500 test server failure")
        conn = Connection(**mock_connection_params)
        pytest.raises(ServerError, conn.make_call, "", "[3, 5]")


def test_get_request_fail():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(400, text="400 test request failure")
        conn = Connection(**mock_connection_params)
        pytest.raises(RequestError, conn.make_call, "")


def test_post_request_fail():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(400, text="400 test request failure")
        conn = Connection(**mock_connection_params)
        pytest.raises(RequestError, conn.make_call, "", "[3, 5]")

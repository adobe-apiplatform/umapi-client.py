# Copyright (c) 2016-2017 Adobe Inc.  All rights reserved.
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
import six
from requests import Session


from conftest import mock_connection_params, MockResponse

from umapi_client import Connection

def test_set_connection_pooling():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])

        params = dict(mock_connection_params)
        params['connection_pooling'] = True

        conn = Connection(**params)
        initial_session = conn.session_manager.session_count
        conn.session_manager.get("")
        assert initial_session == conn.session_manager.session_count

        params['connection_pooling'] = False
        conn = Connection(**params)
        initial_session = conn.session_manager.session_count
        conn.session_manager.get("")
        assert initial_session != conn.session_manager.session_count


def test_get_success():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])

        params = dict(mock_connection_params)
        params['connection_pooling'] = True

        conn = Connection(**params)
        resp_session_manager = conn.session_manager.get("")
        response_session = requests.session().get("")
        assert resp_session_manager == response_session

def test_post_success():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, body=["test", "body"])

        params = dict(mock_connection_params)
        params['connection_pooling'] = True
        conn = Connection(**params)

        resp_session_manager = conn.session_manager.post("","data")
        response_session = requests.session().post("",data="data")
        assert resp_session_manager == response_session

def test_delete_success():
    with mock.patch("umapi_client.connection.requests.Session.delete") as mock_delete:
        mock_delete.return_value = MockResponse(200, body=["test", "body"])

        params = dict(mock_connection_params)
        params['connection_pooling'] = True
        conn = Connection(**params)

        resp_session_manager = conn.session_manager.delete("")
        response_session = requests.session().delete("")
        assert resp_session_manager == response_session

def test_update_session():

    params = dict(mock_connection_params)
    params['connection_pooling'] = True
    conn = Connection(**params)

    session_count = conn.session_manager.session_count
    age = conn.session_manager.session_initialized

    time.sleep(1)
    conn.session_manager.renew_session()

    assert session_count != conn.session_manager.session_count
    assert age != conn.session_manager.session_initialized

def test_validate_session():

    params = dict(mock_connection_params)
    params['connection_pooling'] = True
    conn = Connection(**params)

    original_session = conn.session_manager.session_count
    conn.session_manager.validate_session()
    assert original_session == conn.session_manager.session_count

    conn.session_manager.session_max_age = 4
    time.sleep(5)
    conn.session_manager.validate_session()
    assert  original_session != conn.session_manager.session_count







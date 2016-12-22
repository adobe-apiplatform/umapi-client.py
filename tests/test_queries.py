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

import pytest

import mock

from conftest import mock_connection_params, MockResponse
from umapi_client import Connection, QueryMultiple, ClientError


def test_query_single_success():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success", "object": {"name": "n1", "type": "object"}})
        conn = Connection(**mock_connection_params)
        assert conn.query_single("object", ["n1"]) == {"name": "n1", "type": "object"}


def test_query_single_not_found():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Object not found")
        conn = Connection(**mock_connection_params)
        assert conn.query_single("object", ["n1"]) == {}


def test_query_single_error():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "error"})
        conn = Connection(**mock_connection_params)
        pytest.raises(ClientError, conn.query_single, "object", ["n1"])


def test_query_multiple_success():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n1", "type": "object"},
                                                               {"name": "n2", "type": "object"}]})
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("object") == ([{"name": "n1", "type": "object"},
                                                  {"name": "n2", "type": "object"}],
                                                 False)


def test_query_multiple_empty():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "objects": []})
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("object") == ([], True)


def test_query_multiple_paged():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n1", "type": "object"},
                                                               {"name": "n2", "type": "object"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "objects": [{"name": "n3", "type": "object"},
                                                               {"name": "n4", "type": "object"}]})]
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("object", 0) == ([{"name": "n1", "type": "object"},
                                                     {"name": "n2", "type": "object"}],
                                                    False)
        assert conn.query_multiple("object", 1) == ([{"name": "n3", "type": "object"},
                                                     {"name": "n4", "type": "object"}],
                                                    True)


def test_qm_iterate_complete():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n1", "type": "object"},
                                                               {"name": "n2", "type": "object"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "objects": [{"name": "n3", "type": "object"},
                                                               {"name": "n4", "type": "object"}]})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "object")
        for obj in qm:
            if obj["name"] == "n3":
                break
        assert qm.all_results() == [{"name": "n1", "type": "object"},
                                    {"name": "n2", "type": "object"},
                                    {"name": "n3", "type": "object"},
                                    {"name": "n4", "type": "object"}]


def test_qm_iterate_partial():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n1", "type": "object"},
                                                               {"name": "n2", "type": "object"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n1", "type": "object"},
                                                               {"name": "n2", "type": "object"}]}),
                                MockResponse(200, {"result": "error"})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "object")
        for obj in qm:
            if obj["name"] == "n2":
                break
        for obj in qm:
            if obj["name"] == "n2":
                break
        pytest.raises(ClientError, qm.all_results)


def test_qm_reload():
    with mock.patch("umapi_client.connection.requests.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n1", "type": "object"},
                                                               {"name": "n2", "type": "object"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "objects": [{"name": "n3", "type": "object"},
                                                               {"name": "n4", "type": "object"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "objects": [{"name": "n5", "type": "object"},
                                                               {"name": "n6", "type": "object"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "objects": [{"name": "n7", "type": "object"},
                                                               {"name": "n8", "type": "object"}]})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "object")
        assert list(qm) == [{"name": "n1", "type": "object"},
                            {"name": "n2", "type": "object"},
                            {"name": "n3", "type": "object"},
                            {"name": "n4", "type": "object"}]
        qm.reload()
        assert qm.all_results() == [{"name": "n5", "type": "object"},
                                    {"name": "n6", "type": "object"},
                                    {"name": "n7", "type": "object"},
                                    {"name": "n8", "type": "object"}]

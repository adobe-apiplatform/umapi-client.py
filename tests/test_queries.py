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

import pytest

import mock

from conftest import mock_connection_params, MockResponse
from umapi_client import Connection, QueryMultiple, QuerySingle, ClientError, RequestError


def test_query_single_success():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success", "user": {"name": "n1", "type": "user"}})
        conn = Connection(**mock_connection_params)
        assert conn.query_single("user", ["n1"]) == {"name": "n1", "type": "user"}


def test_query_single_not_found():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Object not found")
        conn = Connection(**mock_connection_params)
        assert conn.query_single("user", ["n1"]) == {}


def test_query_single_error():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "error"})
        conn = Connection(**mock_connection_params)
        pytest.raises(ClientError, conn.query_single, "user", ["n1"])


def test_qs_success():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success",
                                                   "user": {"user": "foo@bar.com", "type": "adobeID"}})
        conn = Connection(**mock_connection_params)
        qs = QuerySingle(conn, "user", ["foo@bar.com"])
        assert qs.result() == {"user": "foo@bar.com", "type": "adobeID"}


def test_qs_not_found():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Object not found")
        conn = Connection(**mock_connection_params)
        qs = QuerySingle(conn, "user", ["foo@bar.com"])
        assert qs.result() == {}


def test_qs_reload():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "user": {"user": "foo1@bar.com", "type": "adobeID"}}),
                                MockResponse(200, {"result": "success",
                                                   "user": {"user": "foo2@bar.com", "type": "adobeID"}})]
        conn = Connection(**mock_connection_params)
        qs = QuerySingle(conn, "user", ["foo@bar.com"])
        assert qs.result() == {"user": "foo1@bar.com", "type": "adobeID"}
        # second verse, same as the first
        assert qs.result() == {"user": "foo1@bar.com", "type": "adobeID"}
        qs.reload()
        assert qs.result() == {"user": "foo2@bar.com", "type": "adobeID"}


def test_query_multiple_user_success():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n1", "type": "user"},
                                                             {"name": "n2", "type": "user"}]})
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user") == ([{"name": "n1", "type": "user"},
                                                {"name": "n2", "type": "user"}],
                                               False)


def test_query_multiple_user_empty():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "users": []})
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user") == ([], True)


def test_query_multiple_user_not_found():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Object not found")
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user") == ([], True)


def test_query_multiple_user_paged():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n1", "type": "user"},
                                                             {"name": "n2", "type": "user"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "users": [{"name": "n3", "type": "user"},
                                                             {"name": "n4", "type": "user"}]})]
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user", 0) == ([{"name": "n1", "type": "user"},
                                                   {"name": "n2", "type": "user"}],
                                                  False)
        assert conn.query_multiple("user", 1) == ([{"name": "n3", "type": "user"},
                                                   {"name": "n4", "type": "user"}],
                                                  True)


def test_qm_user_iterate_complete():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n1", "type": "user"},
                                                             {"name": "n2", "type": "user"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "users": [{"name": "n3", "type": "user"},
                                                             {"name": "n4", "type": "user"}]})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "user")
        for obj in qm:
            if obj["name"] == "n3":
                break
        assert qm.all_results() == [{"name": "n1", "type": "user"},
                                    {"name": "n2", "type": "user"},
                                    {"name": "n3", "type": "user"},
                                    {"name": "n4", "type": "user"}]


def test_qm_user_iterate_partial():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n1", "type": "user"},
                                                             {"name": "n2", "type": "user"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n1", "type": "user"},
                                                             {"name": "n2", "type": "user"}]}),
                                MockResponse(200, {"result": "error"})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "user")
        for obj in qm:
            if obj["name"] == "n2":
                break
        for obj in qm:
            if obj["name"] == "n2":
                break
        pytest.raises(ClientError, qm.all_results)


def test_qm_user_reload():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n1", "type": "user"},
                                                             {"name": "n2", "type": "user"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "users": [{"name": "n3", "type": "user"},
                                                             {"name": "n4", "type": "user"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": False,
                                                   "users": [{"name": "n5", "type": "user"},
                                                             {"name": "n6", "type": "user"}]}),
                                MockResponse(200, {"result": "success",
                                                   "lastPage": True,
                                                   "users": [{"name": "n7", "type": "user"},
                                                             {"name": "n8", "type": "user"}]})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "user")
        assert list(qm) == [{"name": "n1", "type": "user"},
                            {"name": "n2", "type": "user"},
                            {"name": "n3", "type": "user"},
                            {"name": "n4", "type": "user"}]
        qm.reload()
        assert qm.all_results() == [{"name": "n5", "type": "user"},
                                    {"name": "n6", "type": "user"},
                                    {"name": "n7", "type": "user"},
                                    {"name": "n8", "type": "user"}]


def test_query_multiple_usergroup_success():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200,
                                             [{"name": "n1", "type": "user-group"},
                                              {"name": "n2", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "2"})
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user-group") == ([{"name": "n1", "type": "user-group"},
                                                      {"name": "n2", "type": "user-group"}],
                                                     False)


def test_query_multiple_usergroup_empty():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200,
                                             [],
                                             {"X-Total-Count": "0",
                                              "X-Page-Count": "1",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "0"})
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user-group") == ([], True)


def test_query_multiple_usergroup_not_found():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Object not found")
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user-group") == ([], True)


def test_query_multiple_usergroup_paged():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200,
                                             [{"name": "n1", "type": "user-group"},
                                              {"name": "n2", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "2"}),
                                MockResponse(200,
                                             [{"name": "n3", "type": "user-group"},
                                              {"name": "n4", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "2",
                                              "X-Page-Size:": "2"})]
        conn = Connection(**mock_connection_params)
        assert conn.query_multiple("user-group", 0) == ([{"name": "n1", "type": "user-group"},
                                                         {"name": "n2", "type": "user-group"}],
                                                        False)
        assert conn.query_multiple("user-group", 1) == ([{"name": "n3", "type": "user-group"},
                                                         {"name": "n4", "type": "user-group"}],
                                                        True)


def test_qm_usergroup_iterate_complete():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200,
                                             [{"name": "n1", "type": "user-group"},
                                              {"name": "n2", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "2"}),
                                MockResponse(200,
                                             [{"name": "n3", "type": "user-group"},
                                              {"name": "n4", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "2",
                                              "X-Page-Size:": "2"})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "user-group")
        for obj in qm:
            if obj["name"] == "n3":
                break
        assert qm.all_results() == [{"name": "n1", "type": "user-group"},
                                    {"name": "n2", "type": "user-group"},
                                    {"name": "n3", "type": "user-group"},
                                    {"name": "n4", "type": "user-group"}]


def test_qm_usergroup_iterate_partial():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200,
                                             [{"name": "n1", "type": "user-group"},
                                              {"name": "n2", "type": "user-group"}],
                                             {"X-Total-Count": "6",
                                              "X-Page-Count": "3",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "2"}),
                                MockResponse(200,
                                             [{"name": "n1", "type": "user-group"},
                                              {"name": "n2", "type": "user-group"}],
                                             {"X-Total-Count": "6",
                                              "X-Page-Count": "3",
                                              "X-Current-Page": "2",
                                              "X-Page-Size:": "2"}),
                                MockResponse(400, text="400 bad request")]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "user-group")
        for obj in qm:
            if obj["name"] == "n2":
                break
        for obj in qm:
            if obj["name"] == "n2":
                break
        pytest.raises(RequestError, qm.all_results)


def test_qm_usergroup_reload():
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = [MockResponse(200,
                                             [{"name": "n1", "type": "user-group"},
                                              {"name": "n2", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "2"}),
                                MockResponse(200,
                                             [{"name": "n3", "type": "user-group"},
                                              {"name": "n4", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "2",
                                              "X-Page-Size:": "2"}),
                                MockResponse(200,
                                             [{"name": "n5", "type": "user-group"},
                                              {"name": "n6", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "1",
                                              "X-Page-Size:": "2"}),
                                MockResponse(200,
                                             [{"name": "n7", "type": "user-group"},
                                              {"name": "n8", "type": "user-group"}],
                                             {"X-Total-Count": "4",
                                              "X-Page-Count": "2",
                                              "X-Current-Page": "2",
                                              "X-Page-Size:": "2"})]
        conn = Connection(**mock_connection_params)
        qm = QueryMultiple(conn, "user-group")
        assert list(qm) == [{"name": "n1", "type": "user-group"},
                            {"name": "n2", "type": "user-group"},
                            {"name": "n3", "type": "user-group"},
                            {"name": "n4", "type": "user-group"}]
        qm.reload()
        assert qm.all_results() == [{"name": "n5", "type": "user-group"},
                                    {"name": "n6", "type": "user-group"},
                                    {"name": "n7", "type": "user-group"},
                                    {"name": "n8", "type": "user-group"}]

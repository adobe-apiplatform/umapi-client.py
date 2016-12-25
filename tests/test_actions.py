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

import json

import mock

from conftest import mock_connection_params, MockResponse
from umapi_client import Connection, Action


def test_action_create():
    action = Action(frame_name="frame text")
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [], "frame_name": "frame text"}'


def test_action_create_one():
    action = Action(z1="z1 text").append(com1={"com1k": "com1v"})
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"com1": {"com1k": "com1v"}}], "z1": "z1 text"}'


def test_action_create_one_dofirst():
    action = Action(z1="z1 text").insert(com1={"com1k": "com1v"})
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"do": [{"com1": {"com1k": "com1v"}}], "z1": "z1 text"}'


def test_action_create_two():
    action = Action(a1="a1 text", z1="z1 text").append(com1={"com1k": "com1v"}).append(com2={"com2k": "com2v"})
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"a1": "a1 text", "do": [{"com1": {"com1k": "com1v"}}, {"com2": {"com2k": "com2v"}}], "z1": "z1 text"}'


def test_action_create_two_dofirst():
    action = Action(a1="a1 text", z1="z1 text").append(com1={"com1k": "com1v"}).insert(com2={"com2k": "com2v"})
    assert json.dumps(action.wire_dict(), sort_keys=True) == \
           '{"a1": "a1 text", "do": [{"com2": {"com2k": "com2v"}}, {"com1": {"com1k": "com1v"}}], "z1": "z1 text"}'


def test_execute_single_success():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action) == (1, 1)


def test_execute_single_dofirst_success():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").insert(a="a")
        assert conn.execute_single(action) == (1, 1)


def test_execute_multiple_success():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0").append(b="b")
        action1 = Action(top="top1").append(a="a1")
        assert conn.execute_multiple([action0, action1]) == (2, 2)


def test_execute_multiple_dofirst_success():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0").insert(b="b")
        action1 = Action(top="top1").append(a="a1")
        assert conn.execute_multiple([action0, action1]) == (2, 2)


def test_execute_single_error():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "errors": [{"index": 0, "step": 0,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action) == (1, 0)
        assert action.execution_errors() == [{"command": {"a": "a"},
                                              "errorCode": "test.error",
                                              "message": "Test error message"}]


def test_execute_single_multi_error():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "errors": [{"index": 0, "step": 0,
                                                                "errorCode": "error1",
                                                                "message": "message1"},
                                                               {"index": 0, "step": 0,
                                                                "errorCode": "error2",
                                                                "message": "message2"}]})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action) == (1, 0)
        assert action.execution_errors() == [{"command": {"a": "a"},
                                              "errorCode": "error1",
                                              "message": "message1"},
                                             {"command": {"a": "a"},
                                              "errorCode": "error2",
                                              "message": "message2"}]


def test_execute_single_dofirst_error():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "errors": [{"index": 0, "step": 0,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").insert(a="a")
        assert conn.execute_single(action) == (1, 0)
        assert action.execution_errors() == [{"command": {"a": "a"},
                                              "errorCode": "test.error",
                                              "message": "Test error message"}]


def test_execute_multiple_error():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "partial",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 1,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1").append(b="b")
        assert conn.execute_multiple([action0, action1]) == (2, 1)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == [{"command": {"b": "b"},
                                               "errorCode": "test.error",
                                               "message": "Test error message"}]


def test_execute_multiple_multi_error():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 1,
                                                                "errorCode": "error1",
                                                                "message": "message1"},
                                                               {"index": 1, "step": 1,
                                                                "errorCode": "error2",
                                                                "message": "message2"}]})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1").append(b="b")
        assert conn.execute_multiple([action0, action1]) == (2, 1)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == [{"command": {"b": "b"},
                                               "errorCode": "error1",
                                               "message": "message1"},
                                              {"command": {"b": "b"},
                                               "errorCode": "error2",
                                               "message": "message2"}]


def test_execute_multiple_dofirst_error():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 1,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1").insert(b="b")
        assert conn.execute_multiple([action0, action1]) == (2, 1)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == [{"command": {"a": "a1"},
                                               "errorCode": "test.error",
                                               "message": "Test error message"}]


def test_execute_single_throttle_commands():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "partial",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 0, "errorCode": "test"}]})
        conn = Connection(throttle_commands=2, **mock_connection_params)
        action = Action(top="top0").append(a="a0").append(a="a1").append(a="a2")
        assert conn.execute_single(action) == (2, 1)
        assert action.execution_errors() == [{"command": {"a": "a2"}, "errorCode": "test"}]


def test_execute_multiple_throttle_actions():
    with mock.patch("umapi_client.connection.requests.post") as mock_post:
        mock_post.side_effect = [MockResponse(200, {"result": "success"}),
                                 MockResponse(200, {"result": "partial",
                                                    "completed": 0,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 0, "step": 0, "errorCode": "test"}]})]
        conn = Connection(throttle_actions=2, **mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1")
        action2 = Action(top="top2").append(a="a2")
        assert conn.execute_multiple([action0, action1, action2]) == (3, 2)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == []
        assert action2.execution_errors() == [{"command": {"a": "a2"}, "errorCode": "test"}]

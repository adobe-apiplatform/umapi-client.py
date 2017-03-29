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

import mock
import pytest
from conftest import mock_connection_params, MockResponse

from umapi_client import Connection, Action, BatchError


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


def test_execute_single_success_immediate():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action, immediate=True) == (0, 1, 1)


def test_execute_single_success_queued():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(throttle_actions=2, **mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action) == (1, 0, 0)
        assert conn.execute_single(action) == (0, 2, 2)


def test_execute_single_error_queued_throttled():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.side_effect = [MockResponse(200, {"result": "success"}),
                                 MockResponse(200, {"result": "partial",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 0,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})]
        conn = Connection(throttle_actions=2, throttle_commands=1, **mock_connection_params)
        action = Action(top="top").append(a="a").append(b="b").append(c="c").append(d="d")
        assert conn.execute_single(action) == (0, 4, 3)
        assert action.execution_errors() == [{"command": {"d": "d"},
                                              "target": {"top": "top"},
                                              "errorCode": "test.error",
                                              "message": "Test error message"}]


def test_execute_single_error_immediate_throttled():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "partial",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 0, "errorCode": "test"}]})
        conn = Connection(throttle_commands=2, **mock_connection_params)
        action = Action(top="top0").append(a="a0").append(a="a1").append(a="a2")
        assert conn.execute_single(action, immediate=True) == (0, 2, 1)
        assert action.execution_errors() == [{"command": {"a": "a2"}, "target": {"top": "top0"}, "errorCode": "test"}]


def test_execute_single_dofirst_success_immediate():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").insert(a="a")
        assert conn.execute_single(action, immediate=True) == (0, 1, 1)


def test_execute_single_error_immediate():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "errors": [{"index": 0, "step": 0,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action, immediate=True) == (0, 1, 0)
        assert action.execution_errors() == [{"command": {"a": "a"},
                                              "target": {"top": "top"},
                                              "errorCode": "test.error",
                                              "message": "Test error message"}]


def test_execute_single_multi_error_immediate():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "errors": [{"index": 0, "step": 0,
                                                                "errorCode": "error1",
                                                                "message": "message1"},
                                                               {"index": 0, "step": 0,
                                                                "errorCode": "error2",
                                                                "message": "message2"}]})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").append(a="a")
        assert conn.execute_single(action, immediate=True) == (0, 1, 0)
        assert action.execution_errors() == [{"command": {"a": "a"},
                                              "target": {"top": "top"},
                                              "errorCode": "error1",
                                              "message": "message1"},
                                             {"command": {"a": "a"},
                                              "target": {"top": "top"},
                                              "errorCode": "error2",
                                              "message": "message2"}]


def test_execute_single_dofirst_error_immediate():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "errors": [{"index": 0, "step": 0,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action = Action(top="top").insert(a="a")
        assert conn.execute_single(action, immediate=True) == (0, 1, 0)
        assert action.execution_errors() == [{"command": {"a": "a"},
                                              "target": {"top": "top"},
                                              "errorCode": "test.error",
                                              "message": "Test error message"}]


def test_execute_multiple_success():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0").append(b="b")
        action1 = Action(top="top1").append(a="a1")
        assert conn.execute_multiple([action0, action1]) == (0, 2, 2)


def test_execute_multiple_success_queued():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0").append(b="b")
        action1 = Action(top="top1").append(a="a1")
        assert conn.execute_multiple([action0, action1], immediate=False) == (2, 0, 0)
        assert conn.execute_queued() == (0, 2, 2)


def test_execute_multiple_dofirst_success():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0").insert(b="b")
        action1 = Action(top="top1").append(a="a1")
        assert conn.execute_multiple([action0, action1]) == (0, 2, 2)


def test_execute_multiple_error():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "partial",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 1,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1").append(b="b")
        assert conn.execute_multiple([action0, action1]) == (0, 2, 1)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == [{"command": {"b": "b"},
                                               "target": {"top": "top1"},
                                               "errorCode": "test.error",
                                               "message": "Test error message"}]


def test_execute_multiple_multi_error():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
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
        assert conn.execute_multiple([action0, action1]) == (0, 2, 1)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == [{"command": {"b": "b"},
                                               "target": {"top": "top1"},
                                               "errorCode": "error1",
                                               "message": "message1"},
                                              {"command": {"b": "b"},
                                               "target": {"top": "top1"},
                                               "errorCode": "error2",
                                               "message": "message2"}]


def test_execute_multiple_dofirst_error():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "error",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 1, "step": 1,
                                                                "errorCode": "test.error",
                                                                "message": "Test error message"}]})
        conn = Connection(**mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1").insert(b="b")
        assert conn.execute_multiple([action0, action1]) == (0, 2, 1)
        assert action0.execution_errors() == []
        assert action1.execution_errors() == [{"command": {"a": "a1"},
                                               "target": {"top": "top1"},
                                               "errorCode": "test.error",
                                               "message": "Test error message"}]


def test_execute_multiple_single_queued_throttle_actions():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.side_effect = [MockResponse(200, {"result": "success"}),
                                 MockResponse(200, {"result": "partial",
                                                    "completed": 1,
                                                    "notCompleted": 1,
                                                    "errors": [{"index": 0, "step": 0, "errorCode": "test"}]})]
        conn = Connection(throttle_actions=2, **mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1")
        action2 = Action(top="top2").append(a="a2")
        action3 = Action(top="top3").append(a="a3")
        assert conn.execute_multiple([action0, action1, action2], immediate=False) == (1, 2, 2)
        local_status, server_status = conn.status(remote=False)
        assert server_status == {"status": "Never contacted",
                                 "endpoint": conn.endpoint}
        assert local_status == {"multiple-query-count": 0,
                                "single-query-count": 0,
                                "actions-sent": 2,
                                "actions-completed": 2,
                                "actions-queued": 1}
        assert conn.execute_single(action3) == (0, 2, 1)
        local_status, _ = conn.status(remote=False)
        assert local_status == {"multiple-query-count": 0,
                                "single-query-count": 0,
                                "actions-sent": 4,
                                "actions-completed": 3,
                                "actions-queued": 0}
        assert action0.execution_errors() == []
        assert action1.execution_errors() == []
        assert action2.execution_errors() == [{"command": {"a": "a2"}, "target": {"top": "top2"}, "errorCode": "test"}]
        assert action3.execution_errors() == []


def test_execute_multiple_queued_throttle_actions_error():
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.side_effect = [MockResponse(500),
                                 MockResponse(200, {"result": "success"}),
                                 MockResponse(200, {"result": "success"})]
        conn = Connection(throttle_actions=2, **mock_connection_params)
        action0 = Action(top="top0").append(a="a0")
        action1 = Action(top="top1").append(a="a1")
        action2 = Action(top="top2").append(a="a2")
        action3 = Action(top="top3").append(a="a3")
        action4 = Action(top="top4").append(a="a4")
        action5 = Action(top="top5").append(a="a5")
        pytest.raises(BatchError, conn.execute_multiple,
                      [action0, action1, action2, action3, action4, action5], immediate=False)
        local_status, _ = conn.status(remote=False)
        assert local_status == {"multiple-query-count": 0,
                                "single-query-count": 0,
                                "actions-sent": 6,
                                "actions-completed": 4,
                                "actions-queued": 0}

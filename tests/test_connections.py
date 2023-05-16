# Copyright (c) 2016-2021 Adobe Inc.  All rights reserved.
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
from pathlib import Path

from conftest import MockResponse

from umapi_client import Connection
from umapi_client import ArgumentError, UnavailableError, ServerError, RequestError
from umapi_client import UserAction, IdentityType, GroupAction
from umapi_client import __version__ as umapi_version
from umapi_client.auth import JWTAuth


def test_remote_status_success(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body={"build": "2559", "version": "2.1.54", "state": "LIVE"})
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status == {"endpoint": "https://test/", "build": "2559", "version": "2.1.54", "state": "LIVE"}


def test_remote_status_failure(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(404, text="404 Not Found")
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status["status"].startswith("Unexpected")


def test_remote_status_timeout(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = requests.Timeout
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status["status"].startswith("Unreachable")


def test_remote_status_error(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = requests.ConnectionError
        conn = Connection(**mock_connection_params)
        _, remote_status = conn.status(remote=True)
        assert remote_status["status"].startswith("Unreachable")


# log_stream fixture defined in conftest.py
def test_remote_status_error_logging(log_stream, mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = requests.ConnectionError
        stream, logger = log_stream
        conn = Connection(**mock_connection_params)
        conn.logger = logger
        conn.retry_max_attempts = 3
        conn.retry_first_delay = 1
        conn.retry_random_delay = 1
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "")
        stream.flush()
        log = stream.getvalue()  # save as a local so can do pytest -l to see exact log
        assert "code Error on try 1" in log
        assert "code Error on try 2" in log
        assert "code Error on try 3" in log
        assert "code Error on try 4" not in log


def test_ua_string(mock_connection_params):
    conn = Connection(**mock_connection_params)
    req = conn.session.prepare_request(requests.Request('GET', "http://test.com/"))
    ua_header = req.headers.get("User-Agent")
    assert ua_header.startswith("umapi-client/" + umapi_version)
    assert " Python" in ua_header
    req = conn.session.prepare_request(requests.Request('POST', "http://test.com/", data="This is a test"))
    ua_header = req.headers.get("User-Agent")
    assert ua_header.startswith("umapi-client/" + umapi_version)
    assert " Python" in ua_header


def test_ua_string_additional(mock_connection_params):
    conn = Connection(user_agent="additional/1.0", **mock_connection_params)
    req = conn.session.prepare_request(requests.Request('GET', "http://test.com/"))
    ua_header = req.headers.get("User-Agent")
    assert ua_header.startswith("additional/1.0 umapi-client/" + umapi_version)
    req = conn.session.prepare_request(requests.Request('POST', "http://test.com/", data="This is a test"))
    ua_header = req.headers.get("User-Agent")
    assert ua_header.startswith("additional/1.0 umapi-client/" + umapi_version)


def test_mock_proxy_get(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])
        with mock.patch("umapi_client.connection.os.getenv") as mock_getenv:
            mock_getenv.return_value = "proxy"
            conn = Connection(**mock_connection_params)
            conn.make_call("").json()
            mock_get.assert_called_with('http://test/', auth='N/A', timeout=120.0)


def test_mock_playback_get(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])
        with mock.patch("umapi_client.connection.os.getenv") as mock_getenv:
            mock_getenv.return_value = "playback"
            conn = Connection(**mock_connection_params)
            conn.make_call("").json()
            assert mock_get.call_args[0][0] == 'http://test/'
            assert isinstance(mock_get.call_args[1]['auth'], JWTAuth)


def test_mock_proxy_get(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])
        with mock.patch("umapi_client.connection.os.getenv") as mock_getenv:
            mock_getenv.return_value = "error"
            pytest.raises(ArgumentError, Connection, tuple(), mock_connection_params)


def test_get_success(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])
        conn = Connection(**mock_connection_params)
        assert conn.make_call("").json() == ["test", "body"]


def test_get_success_test_mode(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(200, body=["test", "body"])
        conn = Connection(test_mode=True, **mock_connection_params)
        assert conn.make_call("").json() == ["test", "body"]


def test_post_success(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, body=["test", "body"])
        conn = Connection(**mock_connection_params)
        assert conn.make_call("", [3, 5]).json() == ["test", "body"]


def test_post_success_test_mode(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, body=["test", "body"])
        conn = Connection(test_mode=True, **mock_connection_params)
        assert conn.make_call("", [3, 5]).json() == ["test", "body"]


def test_get_timeout(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.side_effect = requests.Timeout
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 4
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "")
        assert mock_get.call_count == 4


def test_post_timeout(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.side_effect = requests.Timeout
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "", [3, 5])
        assert mock_post.call_count == 2


def test_get_retry_header_1(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(429, headers={"Retry-After": "1"})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_header_1(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(429, headers={"Retry-After": "1"})
        conn = Connection(**mock_connection_params)
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


def test_get_retry_header_time_2(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(502, headers={"Retry-After": formatdate(time.time() + 2.5)})
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_header_time_2(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(502, headers={"Retry-After": formatdate(time.time() + 2.5)})
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


def test_get_retry_header_0(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(503, headers={"Retry-After": "0"})
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_header_0(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(503, headers={"Retry-After": "0"})
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


def test_get_retry_no_header(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(504)
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "")


def test_post_retry_no_header(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(504)
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(UnavailableError, conn.make_call, "", "[3, 5]")


# log_stream fixture defined in conftest.py
def test_get_retry_logging(log_stream, mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(429, headers={"Retry-After": "3"})
        stream, logger = log_stream
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 3
        conn.logger = logger
        pytest.raises(UnavailableError, conn.make_call, "")
        stream.flush()
        log = stream.getvalue()  # save as a local so can do pytest -l to see exact log
        assert log == """UMAPI request limit reached (code 429 on try 1)
waiting 3 seconds to continue...
UMAPI request limit reached (code 429 on try 2)
waiting 3 seconds to continue...
UMAPI request limit reached (code 429 on try 3)
UMAPI timeout...giving up after 3 attempts (6 seconds).
"""

# log_stream fixture defined in conftest.py
def test_post_retry_logging(log_stream, mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(429, headers={"Retry-After": "3"})
        stream, logger = log_stream
        params = dict(mock_connection_params)
        conn = Connection(**params)
        conn.logger = logger
        conn.retry_max_attempts = 3
        pytest.raises(UnavailableError, conn.make_call, "", [3, 5])
        stream.flush()
        log = stream.getvalue()  # save as a local so can do pytest -l to see exact log
        assert log == """UMAPI request limit reached (code 429 on try 1)
waiting 3 seconds to continue...
UMAPI request limit reached (code 429 on try 2)
waiting 3 seconds to continue...
UMAPI request limit reached (code 429 on try 3)
UMAPI timeout...giving up after 3 attempts (6 seconds).
"""

def test_get_server_fail(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(500, text="500 test server failure")
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(ServerError, conn.make_call, "")


def test_post_server_fail(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(500, text="500 test server failure")
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(ServerError, conn.make_call, "", "[3, 5]")


def test_get_request_fail(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.get") as mock_get:
        mock_get.return_value = MockResponse(400, text="400 test request failure")
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(RequestError, conn.make_call, "")


def test_post_request_fail(mock_connection_params):
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(400, text="400 test request failure")
        conn = Connection(**mock_connection_params)
        conn.retry_max_attempts = 2
        conn.retry_first_delay = 1
        conn.retry_random_delay = 2
        conn.timeout = 3
        pytest.raises(RequestError, conn.make_call, "", "[3, 5]")


def test_large_group_assignment_split():
    """
    Ensure that large group list can be split into multiple commands
    :return:
    """
    group_prefix = "G"
    add_groups = [group_prefix+str(n+1) for n in range(0, 15)]
    user = UserAction(user="user@example.com")
    user.add_to_groups(groups=add_groups)
    assert user.maybe_split_groups(10) is True
    assert len(user.commands) == 2
    assert user.commands[0]["add"]["group"] == add_groups[0:10]
    assert user.commands[1]["add"]["group"] == add_groups[10:]


def test_large_group_assignment_split_recursive():
    """
    Test group list large enough to trigger recursive split
    :return:
    """
    group_prefix = "G"
    add_groups = [group_prefix+str(n+1) for n in range(0, 100)]
    user = UserAction(user="user@example.com")
    user.add_to_groups(groups=add_groups)
    assert user.maybe_split_groups(10) is True
    assert len(user.commands) == 10


def test_large_group_mix_split():
    """
    Ensure that group split works on add and remove
    Each "add" and "remove" group should be split into 2 groups each
    :return:
    """
    group_prefix = "G"
    add_groups = [group_prefix+str(n+1) for n in range(0, 15)]
    remove_groups = [group_prefix+str(n+1) for n in range(15, 30)]
    user = UserAction(user="user@example.com")
    user.add_to_groups(groups=add_groups) \
        .remove_from_groups(groups=remove_groups)
    assert user.maybe_split_groups(10) is True
    assert len(user.commands) == 4
    assert user.commands[0]["add"]["group"] == add_groups[0:10]
    assert user.commands[1]["add"]["group"] == add_groups[10:]
    assert user.commands[2]["remove"]["group"] == remove_groups[0:10]
    assert user.commands[3]["remove"]["group"] == remove_groups[10:]


def test_large_group_action_split(mock_connection_params):
    """
    Ensure that very large group lists (100+) will be handled appropriately
    Connection.execute_multiple splits commands and splits actions
    Result should be 2 actions, even though we only created one action
    :return:
    """
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        conn = Connection(**mock_connection_params)

        group_prefix = "G"
        add_groups = [group_prefix+str(n+1) for n in range(0, 150)]
        user = UserAction(user="user@example.com")
        user.add_to_groups(groups=add_groups)
        assert conn.execute_single(user, immediate=True) == (0, 2, 2)


def test_group_size_limit(mock_connection_params):
    """
    Test with different 'throttle_groups' value, which governs the max size of the group list before commands are split
    :return:
    """
    with mock.patch("umapi_client.connection.requests.Session.post") as mock_post:
        mock_post.return_value = MockResponse(200, {"result": "success"})
        params = mock_connection_params
        conn = Connection(**params)
        conn.throttle_groups = 5

        group_prefix = "G"
        add_groups = [group_prefix+str(n+1) for n in range(0, 150)]
        user = UserAction(user="user@example.com")
        user.add_to_groups(groups=add_groups)
        assert conn.execute_single(user, immediate=True) == (0, 3, 3)


def test_split_add_user():
    """
    Make sure split doesn't do anything when we have a non-add/remove group action
    :return:
    """
    user = UserAction(user="user@example.com")
    user.create(id_type=IdentityType.enterpriseID, firstname="Example", lastname="User",
                country="US", email="user@example.com")
    user.update(firstname="EXAMPLE")
    assert user.maybe_split_groups(10) is False
    assert len(user.commands) == 2
    assert user.wire_dict() == {'do': [{'createEnterpriseID': {'country': 'US',
                                                               'email': 'user@example.com',
                                                               'firstname': 'Example',
                                                               'lastname': 'User',
                                                               'option': 'ignoreIfAlreadyExists'}},
                                       {'update': {'firstname': 'EXAMPLE'}}],
                                'user': 'user@example.com'}


def test_no_group_split():
    """
    maybe_split should return false if nothing was split
    :return:
    """
    group_prefix = "G"
    add_groups = [group_prefix+str(n+1) for n in range(0, 5)]
    user = UserAction(user="user@example.com")
    user.add_to_groups(groups=add_groups)
    assert user.maybe_split_groups(10) is False
    assert len(user.commands) == 1


def test_split_remove_all():
    """
    Don't split groups if "remove" is "all" instead of list
    :return:
    """
    group_prefix = "G"
    add_groups = [group_prefix+str(n+1) for n in range(0, 11)]
    user = UserAction(user="user@example.com")
    user.remove_from_groups(all_groups=True)
    assert user.maybe_split_groups(1) is False
    assert user.wire_dict() == {'do': [{'remove': 'all'}], 'user': 'user@example.com'}
    user.add_to_groups(groups=add_groups)
    assert user.maybe_split_groups(10) is True
    assert user.wire_dict() == {'do': [{'remove': 'all'},
                                       {'add': {'group': ['G1',
                                                            'G2',
                                                            'G3',
                                                            'G4',
                                                            'G5',
                                                            'G6',
                                                            'G7',
                                                            'G8',
                                                            'G9',
                                                            'G10']}},
                                       {'add': {'group': ['G11']}}],
                                'user': 'user@example.com'}


def test_split_group_action():
    user_template = "user.{}@example.com"
    add_users = [user_template.format(n+1) for n in range(0, 25)]
    group = GroupAction(group_name="Test Group")
    group.add_users(users=add_users)
    assert group.maybe_split_groups(10) is True
    assert len(group.commands) == 3

def test_jwt(fixture_dir):
    # make sure we get no errors when constructing a JWT
    with open(Path(fixture_dir) / 'private.key') as keyfile:
        auth = JWTAuth('xxxxxx', 'xxxxx', 'example.com', 'xxxxx', keyfile.read())
        auth.jwt_token()

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

import logging
import re
import os

import pytest
import yaml
import six

import umapi_client

# this test relies on a sensitive configuraition
config_file_name = "local/live_configuration.yaml"
pytestmark = pytest.mark.skipif(not os.access(config_file_name, os.R_OK),
                                reason="Live config file '{}' not found.".format(config_file_name))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


@pytest.fixture(scope="module")
def config():
    with open(config_file_name, "r") as f:
        config = yaml.load(f)
    creds = config["test_org"]
    conn = umapi_client.Connection(org_id=creds["org_id"], auth_dict=creds)
    return conn, config


def test_status(config):
    conn, _ = config
    _, status = conn.status(remote=True)
    logging.info("Server status is %s", status)
    assert status["state"] == "LIVE"


def test_list_users(config):
    conn, _ = config
    users = umapi_client.UsersQuery(connection=conn, in_domain="")
    user_count = 0
    for user in users:
        email = user.get("email", "")
        if re.match(r".*@adobe.com$", str(email).lower()):
            assert str(user["type"]) == "adobeID"
        user_count += 1
        if user_count >= 2000:
            logging.info("Quitting enumeration after 2000 users.")
            break
    logging.info("Found %d users.", user_count)

def test_list_groups(config):
    conn, params = config
    groups = umapi_client.GroupsQuery(connection=conn)
    group_count = 0
    for group in groups:
        name = group.get("groupName")
        member_count = group.get("memberCount", -1)
        logging.info("Group %s has %d members.", name, member_count)
        assert member_count >= 0
        group_count += 1
    logging.info("Found %d groups.", group_count)
    groups.reload()
    group_count_2 = len(groups.all_results())
    assert group_count == group_count_2

def test_get_user(config):
    conn, params = config
    user_query = umapi_client.UserQuery(conn, params["test_user"]["email"])
    user = user_query.result()
    logging.info("User: %s", user)
    for k, v in six.iteritems(params["test_user"]):
        assert user[k].lower() == v.lower()

def test_rename_user(config):
    conn, params = config
    user = umapi_client.UserAction(id_type=params["test_user"]["type"],
                                   email=params["test_user"]["email"],
                                   username=params["test_user"]["username"])
    user.update(first_name="Rodney", last_name="Danger")
    user.update(first_name=params["test_user"]["firstname"], last_name=params["test_user"]["lastname"])
    assert (0, 1, 1) == conn.execute_single(user, immediate=True)

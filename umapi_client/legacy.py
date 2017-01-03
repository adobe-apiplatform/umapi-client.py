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
"""
Legacy UMAPI api from version 1.0 of this library, for backward compatibility.
Clients are strongly encouraged to move to the current version of the API.
"""
# TODO: remove this file when all clients have migrated

import logging
from email.utils import parsedate_tz, mktime_tz
from math import pow
from random import randint
from sys import maxsize
from time import time, sleep

import requests
import six

from .api import Action as NewAction
from .connection import Connection
from .error import RequestError, ServerError, UnavailableError

# make the retry options module-global so they can be set by clients
retry_max_attempts = 4
retry_exponential_backoff_factor = 15  # seconds
retry_random_delay_max = 5  # seconds

# make the logger module-global so it can be set by clients
logger = logging.getLogger(__name__)


class Action(NewAction):
    """
    Here for compatibility with legacy clients only - DO NOT USE!!!
    """
    def __init__(self, user=None, user_key=None, **kwargs):
        if user is None and user_key is None:
            ValueError("Must specify one of user or user_key")
        if user and user_key:
            ValueError("Must specify only one of user or user_key")
        if user_key:
            user = user_key
        NewAction.__init__(self, user=user, **kwargs)

    def do(self, **kwargs):
        """
        Here for compatibility with legacy clients only - DO NOT USE!!!
        This is sort of mix of "append" and "insert": it puts commands in the list,
        with some half smarts about which commands go at the front or back.
        If you add multiple commands to the back in one call, they will get added sorted by command name.
        :param kwargs: the commands in key=val format
        :return: the Action, so you can do Action(...).do(...).do(...)
        """
        # add "create" / "add" / "removeFrom" first
        for k, v in list(six.iteritems(kwargs)):
            if k.startswith("create") or k.startswith("addAdobe") or k.startswith("removeFrom"):
                self.commands.append({k: v})
                del kwargs[k]

        # now do the other actions, in a canonical order (to avoid py2/py3 variations)
        for k, v in sorted(six.iteritems(kwargs)):
            if k in ['add', 'remove']:
                self.commands.append({k: {"product": v}})
            else:
                self.commands.append({k: v})
        return self


class UMAPI:
    """
    This is here for legacy compatibility ONLY -- DO NOT USE!!!

    The UMAPI object is an authenticated connection that doesn't know the
    organization it was authenticated against, which makes no sense.
    This re-implementation uses a connection under the covers, and it
    carefully checks to see that you are using the connection against
    the right organization!
    """
    def __init__(self, endpoint=None, auth=None, test_mode=False, conn=None, **kwargs):
        if isinstance(conn, Connection) and (endpoint is None) and (auth is None):
            # given a connection, remember the org_id it's for.
            self.conn = conn
            self.org_id = conn.org_id
        elif auth and endpoint and (conn is None):
            # wait until we have an org_id to make the connection
            self.conn = None
            self.org_id = None
            self.conn_options = dict(kwargs)
            self.auth = auth
            self.endpoint = str(endpoint)
            self.test_mode = test_mode
        else:
            ValueError("UMAPI create: you must specify either auth and endpoint, or conn, but not both")

    def _get_conn(self, org_id):
        if not self.conn:
            self.org_id = org_id
            self.conn = Connection(org_id=org_id, auth=self.auth,
                                   user_management_endpoint=self.endpoint,
                                   test_mode=self.test_mode,
                                   **self.conn_options)
        else:
            if org_id != self.org_id:
                ValueError("OrganizationID (%s) does not match that in access token (%s)", org_id, self.org_id)

    def users(self, org_id, page=0):
        self._get_conn(org_id)
        return self._call('/users/%s/%d' % (org_id, page), requests.get)

    def groups(self, org_id, page=0):
        self._get_conn(org_id)
        return self._call('/groups/%s/%d' % (org_id, page), requests.get)

    def action(self, org_id, action):
        self._get_conn(org_id)
        if not isinstance(action, Action):
            if not isinstance(action, str) and (hasattr(action, "__getitem__") or hasattr(action, "__iter__")):
                actions = [a.wire_dict() for a in action]
            else:
                raise ActionFormatError("action must be iterable, indexable or Action object")
        else:
            actions = [action.wire_dict()]
        if self.test_mode:
            return self._call('/action/%s?testOnly=true' % org_id, requests.post, actions)
        else:
            return self._call('/action/%s' % org_id, requests.post, actions)

    def _call(self, method, call, params=None):
        assert (call is requests.get) is (params is None)
        try:
            res = self.conn.make_call(method, params)
            if res.status_code == 200:
                result = res.json()
                if "result" in result:
                    if result["result"] == "error":
                        raise UMAPIRequestError(result["errors"][0]["errorCode"])
                    else:
                        return result
                else:
                    raise UMAPIRequestError("Request Error -- Unknown Result Status")
        except UnavailableError as ue:
            raise UMAPIRetryError(ue.result)
        except (RequestError, ServerError) as e:
            raise UMAPIError(e.result)


class UMAPIError(Exception):
    def __init__(self, res):
        Exception.__init__(self, "UMAPI Error: "+str(res.status_code))
        self.res = res


class UMAPIRetryError(Exception):
    def __init__(self, res):
        Exception.__init__(self, "UMAPI Error: "+str(res.status_code))
        self.res = res


class UMAPIRequestError(Exception):
    def __init__(self, code):
        Exception.__init__(self, "Request Error -- %s" % code)
        self.code = code


class ActionFormatError(Exception):
    pass


def paginate(query, org_id, max_pages=maxsize, max_records=maxsize):
    """
    Paginate through all results of a UMAPI query
    :param query: a query method from a UMAPI instance (callable as a function)
    :param org_id: the organization being queried
    :param max_pages: the max number of pages to collect before returning (default all)
    :param max_records: the max number of records to collect before returning (default all)
    :return: the queried records
    """
    page_count = 0
    record_count = 0
    records = []
    while page_count < max_pages and record_count < max_records:
        res = make_call(query, org_id, page_count)
        page_count += 1
        # the following incredibly ugly piece of code is very fragile.
        # the problem is that we are a "dumb helper" that doesn't understand
        # the semantics of the UMAPI or know which query we were given.
        if "groups" in res:
            records += res["groups"]
        elif "users" in res:
            records += res["users"]
        record_count = len(records)
        if res.get("lastPage"):
            break
    return records


def make_call(query, org_id, page):
    """
    Make a single UMAPI call with error handling and server-controlled throttling.
    (Adapted from sample code at https://www.adobe.io/products/usermanagement/docs/samples#retry)
    :param query: a query method from a UMAPI instance (callable as a function)
    :param org_id: the organization being queried
    :param page: the page number of the desired result set
    :return: the json (dictionary) received from the server (if any)
    """
    wait_time = 0
    num_attempts = 0

    while num_attempts < retry_max_attempts:
        if wait_time > 0:
            sleep(wait_time)
            wait_time = 0
        try:
            num_attempts += 1
            return query(org_id, page)
        except UMAPIRetryError as e:
            logger.warning("UMAPI service temporarily unavailable (attempt %d) -- %s", num_attempts, e.res.status_code)
            if "Retry-After" in e.res.headers:
                advice = e.res.headers["Retry-After"]
                advised_time = parsedate_tz(advice)
                if advised_time is not None:
                    # header contains date
                    wait_time = int(mktime_tz(advised_time) - time())
                else:
                    # header contains delta seconds
                    wait_time = int(advice)
            if wait_time <= 0:
                # use exponential back-off with random delay
                delay = randint(0, retry_random_delay_max)
                wait_time = (int(pow(2, num_attempts)) * retry_exponential_backoff_factor) + delay
            logger.warning("Next retry in %d seconds...", wait_time)
            continue
        except UMAPIRequestError as e:
            logger.warning("UMAPI error processing request -- %s", e.code)
            return {}
        except UMAPIError as e:
            logger.warning("HTTP error processing request -- %s: %s", e.res.status_code, e.res.text)
            return {}
    logger.error("UMAPI timeout...giving up on results page %d after %d attempts.", page, retry_max_attempts)
    return {}

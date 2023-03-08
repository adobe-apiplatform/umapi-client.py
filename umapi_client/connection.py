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

import json
import logging
import os
from email.utils import parsedate_tz, mktime_tz
from platform import python_version, version as platform_version
from random import randint
from time import time, sleep, gmtime, strftime
from uuid import uuid4
from datetime import datetime
import requests
import io
import urllib.parse as urlparse

from .auth import JWTAuth
from .error import BatchError, UnavailableError, ClientError, RequestError, ServerError, ArgumentError
from .version import __version__ as umapi_version


class APIResult:
    success_codes = [200, 201, 204]
    timeout_codes = [429, 502, 503, 504]
    client_error = lambda self, x: 201 <= x < 200
    request_error = lambda self, x: 400 <= x < 500

    def __init__(self, result=None, success=False, timeout=None):
        self.result = result
        self.success = success
        self.timeout = timeout
        self.status_code = result.status_code if hasattr(result, 'status_code') else 'Error'

    def check_result(self):
        if self.result.status_code in self.success_codes:
            self.success = True
            return self
        if self.result.status_code in self.timeout_codes:
            self.success = False
            self.timeout = self.get_timeout()
            return self
        if self.client_error(self.result.status_code):
            raise ClientError("Unexpected HTTP Status {:d}: {}".format(self.result.status_code, self.result.text), self.result)
        if self.request_error(self.result.status_code):
            raise RequestError(self.result)
        raise ServerError(self.result)

    def get_timeout(self):
        if "Retry-After" in self.result.headers:
            advice = self.result.headers["Retry-After"]
            advised_time = parsedate_tz(advice)
            if advised_time is not None:
                # header contains date
                return int(mktime_tz(advised_time) - time())
            else:
                # header contains delta seconds
                return int(advice)
        return 0

class Connection:
    """
    An org-specific, authenticated connection to the UMAPI service.  Each method
    makes a single call on the endpoint and returns the result (or raises an error).
    """
    mock_env_var = "UMAPI_MOCK"

    def __init__(self,
                 org_id,
                 auth,
                 endpoint="https://usermanagement.adobe.io/v2/usermanagement",
                 test_mode=False,
                 ssl_verify=True,
                 timeout=120.0,
                 max_retries=4,
                 user_agent=None):
        """
        Open a connection for the given parameters that has the given options.
        The connection is authenticated and the auth token reused on all calls.

        Required parameters.
        :param org_id: string OrganizationID from Adobe.IO integration data
        :param auth: a umapi_client.auth object that handles authentication

        Optional connection parameters (defaults are for Adobe production):
        :param endpoint: the User Management API service root endpoint

        Behavioral options for the connection:
        :param test_mode: Whether to pass the server-side "test mode" flag when executing actions
        :param timeout: How many seconds to wait for server response (<= 0 or None means forever)
        :param ssl_verify:
        """
        self.logger = logging.getLogger(__name__)
        # for testing we mock the server, either by using an http relay
        # which relays and records the requests and responses, or by
        # using a robot which plays back a previously recorded run.
        mock_spec = os.getenv(self.mock_env_var, None)
        if mock_spec:
            if mock_spec not in ["proxy", "playback"]:
                raise ArgumentError("Unknown value for %s: %s" % (self.mock_env_var, mock_spec))
            self.logger.warning("%s override specified as '%s'", self.mock_env_var, mock_spec)
            # mocked servers don't support https
            if endpoint.lower().startswith("https://"):
                endpoint = "http" + endpoint[5:]
            # playback servers don't use authentication
            if mock_spec == "playback":
                auth = JWTAuth("mock", "mock", "mock", "mock", "mock")

        self.org_id = str(org_id)
        self.auth = auth
        self.endpoint = endpoint
        self.test_mode = test_mode
        self.retry_max_attempts = max_retries
        self.retry_first_delay = 15
        self.retry_random_delay = 5
        self.ssl_verify = ssl_verify
        self.timeout = float(timeout) if timeout and float(timeout) > 0.0 else None
        self.throttle_actions = 10
        self.throttle_commands = 10
        self.throttle_groups = 10
        self.action_queue = []
        self.local_status = {"multiple-query-count": 0,
                             "single-query-count": 0,
                             "actions-sent": 0,
                             "actions-completed": 0,
                             "actions-queued": 0}
        self.server_status = {"status": "Never contacted",
                              "endpoint": self.endpoint}
        self.sync_started = False
        self.sync_ended = False
        self.session = requests.Session()
        ua_string = "umapi-client/" + umapi_version + " Python/" + python_version() + " (" + platform_version() + ")"
        if user_agent and user_agent.strip():
            ua_string = user_agent.strip() + " " + ua_string
        self.session.headers["User-Agent"] = ua_string
        self.uuid = str(uuid4())

    def status(self, remote=False):
        """
        Return the connection status, both locally and remotely.

        The local connection status is a dictionary that gives:
        * the count of multiple queries sent to the server.
        * the count of single queries sent to the server.
        * the count of actions sent to the server.
        * the count of actions executed successfully by the server.
        * the count of actions queued to go to the server.

        The remote connection status includes whether the server is live,
        as well as data about version and build.  The server data is
        cached, unless the remote flag is specified.

        :param remote: whether to query the server for its latest status
        :return: tuple of status dicts: (local, server).
        """
        if remote:
            components = urlparse.urlparse(self.endpoint)
            try:
                result = self.session.get(components[0] + "://" + components[1] + "/status", timeout=self.timeout,
                                          verify=self.ssl_verify)
            except Exception as e:
                self.logger.debug("Failed to connect to server for status: %s", e)
                result = None
            if result and result.status_code == 200:
                self.server_status = result.json()
                self.server_status["endpoint"] = self.endpoint
            elif result:
                self.logger.debug("Server status response not understandable: Status: %d, Body: %s",
                             result.status_code, result.text)
                self.server_status = {"endpoint": self.endpoint,
                                      "status": ("Unexpected HTTP status " + str(result.status_code) + " at: " +
                                                 strftime("%d %b %Y %H:%M:%S +0000", gmtime()))}
            else:
                self.server_status = {"endpoint": self.endpoint,
                                      "status": "Unreachable at: " + strftime("%d %b %Y %H:%M:%S +0000", gmtime())}
        return self.local_status, self.server_status

    def query_single(self, object_type, url_params, query_params=None):
        # type: (str, list, dict) -> dict
        """
        Query for a single object.
        :param object_type: string query type (e.g., "users" or "groups")
        :param url_params: required list of strings to provide as additional URL components
        :param query_params: optional dictionary of query options
        :return: the found object (a dictionary), which is empty if none were found
        """
        # Server API convention (v2) is that the pluralized object type goes into the endpoint
        # but the object type is the key in the response dictionary for the returned object.
        self.local_status["single-query-count"] += 1
        query_type = object_type + "s"  # poor man's plural
        query_path = "/organizations/{}/{}".format(self.org_id, query_type)
        for component in url_params if url_params else []:
            query_path += "/" + urlparse.quote(component, safe='/@')
        if query_params: query_path += "?" + urlparse.urlencode(query_params)
        try:
            result = self.make_call(query_path)
            body = result.json()
        except RequestError as re:
            if re.result.status_code == 404:
                self.logger.debug("Ran %s query: %s %s (0 found)",
                             object_type, url_params, query_params)
                return {}
            else:
                raise re
        if body.get("result") == "success":
            value = body.get(object_type, {})
            self.logger.debug("Ran %s query: %s %s (1 found)", object_type, url_params, query_params)
            return value
        else:
            raise ClientError("OK status but no 'success' result", result)

    def query_multiple(self, object_type, page=0, url_params=None, query_params=None):
        # type: (str, int, list, dict) -> tuple
        """
        Query for a page of objects.  Defaults to the (0-based) first page.
        Sadly, the sort order is undetermined.
        :param object_type: string constant query type: either "user" or "group")
        :param page: numeric page (0-based) of results to get (up to 200 in a page)
        :param url_params: optional list of strings to provide as additional URL components
        :param query_params: optional dictionary of query options
        :return: tuple (list of returned dictionaries (one for each query result), bool for whether this is last page)
        """
        # As of 2017-10-01, we are moving to to different URLs for user and user-group queries,
        # and these endpoints have different conventions for pagination.  For the time being,
        # we are also preserving the more general "group" query capability.
        self.local_status["multiple-query-count"] += 1
        if object_type in ("user", "group"):
            query_path = "/{}s/{}/{:d}".format(object_type, self.org_id, page)
            if url_params: query_path += "/" + "/".join([urlparse.quote(c) for c in url_params])
            if query_params: query_path += "?" + urlparse.urlencode(query_params)
        elif object_type == "user-group":
            query_path = "/{}/user-groups".format(self.org_id)
            if url_params: query_path += "/" + "/".join([urlparse.quote(c) for c in url_params])
            query_path += "?page={:d}".format(page+1)
            if query_params: query_path += "&" + urlparse.urlencode(query_params)
        else:
            raise ArgumentError("Unknown query object type ({}): must be 'user' or 'group'".format(object_type))
        try:
            result = self.make_call(query_path)
            body = result.json()
        except RequestError as re:
            if re.result.status_code == 404:
                self.logger.debug("Ran %s query: %s %s (0 found)",
                             object_type, url_params, query_params)
                return [], True, 0, 0, 0, 0
            else:
                raise re

        headers = {k.lower(): v for k, v in result.headers.items()}
        total_count = headers.get("x-total-count", "0")
        page_count = headers.get("x-page-count", "0")
        page_number = headers.get("x-current-page", "1")
        page_size = headers.get("x-page-size", "0")

        if object_type in ("user", "group"):
            if body.get("result") == "success":
                values = body.get(object_type + "s", [])
                last_page = body.get("lastPage", False)

                self.logger.debug("Ran multi-%s query: %s %s (page %d: %d found)",
                             object_type, url_params, query_params, page, len(values))
                return values, last_page, int(total_count), int(page_count), int(page_number), int(page_size)
            else:
                raise ClientError("OK status but no 'success' result", result)
        elif object_type == "user-group":
            self.logger.debug("Ran multi-group query: %s %s (page %d: %d found)",
                         url_params, query_params, page, len(body))
            return body, int(page_number) >= int(page_count), int(total_count), int(page_count), \
                   int(page_number), int(page_size)
        else:
            # this would actually be caught above, but we use a parallel construction in both places
            # to make it easy to add query object types
            raise ArgumentError("Unknown query object type ({}): must be 'user' or 'group'".format(object_type))

    def execute_single(self, action, immediate=False):
        """
        Execute a single action (containing commands on a single object).
        Normally, since actions are batched so as to be most efficient about execution,
        but if you want this command sent immediately (and all prior queued commands
        sent earlier in this command's batch), specify a True value for the immediate flag.

        Since any command can fill the current batch, your command may be submitted
        even if you don't specify the immediate flag.  So don't think of this always
        being a queue call if immedidate=False.

        Returns the number of actions in the queue, that got sent, and that executed successfully.

        :param action: the Action to be executed
        :param immediate: whether the Action should be executed immediately
        :return: the number of actions in the queue, that got sent, and that executed successfully.
        """
        return self.execute_multiple([action], immediate=immediate)

    def execute_queued(self):
        """
        Force execute any queued commands.
        :return: the number of actions left in the queue, that got sent, and that executed successfully.
        """
        return self.execute_multiple([], immediate=True)

    def execute_multiple(self, actions, immediate=True):
        """
        Execute multiple Actions (each containing commands on a single object).
        Normally, the actions are sent for execution immediately (possibly preceded
        by earlier queued commands), but if you are going for maximum efficiency
        you can set immediate=False which will cause the connection to wait
        and batch as many actions as allowed in each server call.

        Since any command can fill the current batch, one or more of your commands may be submitted
        even if you don't specify the immediate flag.  So don't think of this call as always
        being a queue call when immedidate=False.

        Returns the number of actions left in the queue, that got sent, and that executed successfully.

        NOTE: This is where we throttle the number of commands per action.  So the number
        of actions we were given may not be the same as the number we queue or send to the server.
        
        NOTE: If the server gives us a response we don't understand, we note that and continue
        processing as usual.  Then, at the end of the batch, we throw in order to warn the client
        that we had a problem understanding the server.

        :param actions: the list of Action objects to be executed
        :param immediate: whether to immediately send them to the server
        :return: tuple: the number of actions in the queue, that got sent, and that executed successfully.
        """
        # throttling part 1: split up each action into smaller actions, as needed
        # optionally split large lists of groups in add/remove commands (if action supports it)
        split_actions = []
        exceptions = []
        for a in actions:
            if len(a.commands) == 0:
                self.logger.warning("Sending action with no commands: %s", a.frame)
            # maybe_split_groups is a UserAction attribute, so the call may throw an AttributeError
            try:
                if a.maybe_split_groups(self.throttle_groups):
                    self.logger.debug(
                        "Throttling actions %s to have a maximum of %d entries in group lists.",
                        a.frame, self.throttle_groups)
            except AttributeError:
                pass
            if len(a.commands) > self.throttle_commands:
                self.logger.debug("Throttling action %s to have a maximum of %d commands.",
                                                  a.frame, self.throttle_commands)
                split_actions += a.split(self.throttle_commands)
            else:
                split_actions.append(a)
        actions = self.action_queue + split_actions
        # throttling part 2: execute the action list in batches, as needed
        sent = completed = 0
        batch_size = self.throttle_actions
        min_size = 1 if immediate else batch_size
        while len(actions) >= min_size:
            batch, actions = actions[0:batch_size], actions[batch_size:]
            self.logger.debug("Executing %d actions (%d remaining).", len(batch), len(actions))
            sent += len(batch)
            try:
                completed += self._execute_batch(batch)
            except Exception as e:
                exceptions.append(e)
        self.action_queue = actions
        self.local_status["actions-queued"] = queued = len(actions)
        self.local_status["actions-sent"] += sent
        self.local_status["actions-completed"] += completed
        if exceptions:
            raise BatchError(exceptions, queued, sent, completed)
        return queued, sent, completed

    def start_sync(self):
        """Signal the beginning of a sync operation
        Sends a header with the first batch of UMAPI actions"""
        self.sync_started = True

    def end_sync(self):
        """Signal the end of a sync operation
        Sends a header with the next batch of UMAPI actions"""
        self.sync_ended = True

    def _execute_batch(self, actions):
        """
        Execute a single batch of Actions.
        For each action that has a problem, we annotate the action with the
        error information for that action, and we return the number of
        successful actions in the batch.
        :param actions: the list of Action objects to be executed
        :return: count of successful actions
        """
        wire_form = [a.wire_dict() for a in actions]
        if self.test_mode:
            result = self.make_call("/action/%s?testOnly=true" % self.org_id, wire_form)
        else:
            result = self.make_call("/action/%s" % self.org_id, wire_form)
        body = result.json()
        if body.get("errors", None) is None:
            if body.get("result") != "success":
                self.logger.warning("Server action result: no errors, but no success:\n%s", body)
            return len(actions)
        try:
            if body.get("result") == "success":
                self.logger.warning("Server action result: errors, but success report:\n%s", body)
            for error in body["errors"]:
                actions[error["index"]].report_command_error(error)
        except:
            raise ClientError(str(body), result)
        return body.get("completed", 0)

    def make_call(self, path, body=None, delete=False):
        """
        Make a single UMAPI call with error handling and retry on temporary failure.
        :param path: the string endpoint path for the call
        :param body: (optional) list of dictionaries to be serialized into the request body
        :return: the requests.result object (on 200 response), raise error otherwise
        """
        extra_headers = {"X-Request-Id": f"{self.uuid}_{int(datetime.now().timestamp()*1000)}"}
        # if the sync_started or sync_ended flags are set, send a header for any type of call
        if self.sync_started:
            self.logger.info("Sending start_sync signal")
            extra_headers['Pragma'] = 'umapi-sync-start'
            self.sync_started = False
        elif self.sync_ended:
            self.logger.info("Sending end_sync signal")
            extra_headers['Pragma'] = 'umapi-sync-end'
            self.sync_ended = False
        if body:
            request_body = json.dumps(body)
            def call():
                return self.session.post(self.endpoint + path, auth=self.auth, data=request_body, timeout=self.timeout,
                                         verify=self.ssl_verify, headers=extra_headers)
        else:
            if not delete:
                def call():
                    return self.session.get(self.endpoint + path, auth=self.auth, timeout=self.timeout,
                                            verify=self.ssl_verify, headers=extra_headers)
            else:
                def call():
                    return self.session.delete(self.endpoint + path, auth=self.auth, timeout=self.timeout,
                                               verify=self.ssl_verify, headers=extra_headers)

        start_time = time()
        result = None
        for num_attempts in range(1, self.retry_max_attempts + 1):
            checked_result = None
            try:
                result = call()
                checked_result = APIResult(result).check_result()
            except requests.Timeout:
                self.logger.warning("UMAPI connection timeout...(%d seconds on try %d)",
                               self.timeout, num_attempts)
                checked_result = APIResult(success=False, timeout=0)
            except requests.ConnectionError:
                self.logger.warning("UMAPI connection error...(%d seconds on try %d)",
                               self.timeout, num_attempts)
                checked_result = APIResult(success=False, timeout=0)
            
            if checked_result.success:
                return result

            self.logger.warning("UMAPI request limit reached (code %s on try %d)",
                           checked_result.status_code, num_attempts)

            retry_wait = checked_result.timeout
            if retry_wait <= 0:
                # use exponential back-off with random delay
                delay = randint(0, self.retry_random_delay)
                retry_wait = (int(pow(2, num_attempts - 1)) * self.retry_first_delay) + delay

            if num_attempts < self.retry_max_attempts:
                if retry_wait > 0:
                    self.logger.warning("waiting %d seconds to continue...", retry_wait)
                    sleep(retry_wait)
                else:
                    self.logger.warning("Immediate retry...")
        total_time = int(time() - start_time)
        self.logger.error("UMAPI timeout...giving up after %d attempts (%d seconds).",
                     self.retry_max_attempts, total_time)
        raise UnavailableError(self.retry_max_attempts, total_time, checked_result.result)

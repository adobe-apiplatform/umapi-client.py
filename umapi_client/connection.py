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
import logging
from email.utils import parsedate_tz, mktime_tz
from platform import python_version, version as platform_version
from random import randint
from time import time, sleep, gmtime, strftime

import requests
import six
import six.moves.urllib.parse as urlparse

from .auth import JWT, Auth, AccessRequest
from .error import BatchError, UnavailableError, ClientError, RequestError, ServerError
from .version import __version__ as umapi_version


class Connection:
    """
    An org-specific, authorized connection to the UMAPI service.  Each method
    makes a single call on the endpoint and returns the result (or raises an error).
    """

    def __init__(self,
                 org_id,
                 auth_dict=None,
                 auth=None,
                 ims_host="ims-na1.adobelogin.com",
                 ims_endpoint_jwt="/ims/exchange/jwt/",
                 user_management_endpoint="https://usermanagement.adobe.io/v2/usermanagement",
                 test_mode=False,
                 logger=logging.getLogger("umapi_client"),
                 retry_max_attempts=4,
                 retry_first_delay=15,
                 retry_random_delay=5,
                 timeout_seconds=120.0,
                 throttle_actions=10,
                 throttle_commands=10,
                 user_agent=None,
                 **kwargs):
        """
        Open a connection for the given parameters that has the given options.
        The connection is authorized and the auth token reused on all calls.

        Required parameters.  You must specify org_id and one of auth *or* auth_dict
        :param org_id: string OrganizationID from Adobe.IO integration data
        :param auth_dict: a dictionary with auth information (see below)
        :param auth: a umapi_client.auth.Auth object containing authorization

        Auth data: if you supply an auth_dict, it must have values for these keys:
        :param tech_acct_id: string technical account ID from Adobe.IO integration data
        :param api_key: string api_key from Adobe.IO integration data
        :param client_secret: string client secret from Adobe.IO integration data
        and one of:
        :param private_key_file: path to local private key file that matches Adobe.IO public key for integration
        or:
        :param private_key_data: the contents of the private_key_file (PEM format)
        (NOTE: for compatibility with User Sync config files, the key names priv_key_path and tech_acct
         are accepted as aliases for private_key_file and tech_acct_id, respectively.)

        Optional connection parameters (defaults are for Adobe production):
        :param ims_host: the IMS host which will exchange your JWT for an access token
        :param ims_endpoint_jwt: the exchange token endpoint on the IMS host
        :param user_management_endpoint: the User Management API service root endpoint

        Behavioral options for the connection:
        :param test_mode: Whether to pass the server-side "test mode" flag when executing actions
        :param logger: The log handler to use (None suppresses logging, default is named "umapi_client")
        :param retry_max_attempts: How many times to retry on temporary errors
        :param retry_first_delay: The time to delay first retry (grows exponentially from there)
        :param retry_random_delay: The max random delay to add on each exponential backoff retry
        :param timeout_seconds: How many seconds to wait for server response (<= 0 or None means forever)
        :param throttle_actions: Max number of actions to pack into a single call
        :param throttle_commands: Max number of commands allowed in a single action
        :param user_agent: (optional) string to use as User-Agent header (umapi-client/version data will be added)

        Additional keywords are allowed to make it easy to pass a big dictionary with other values
        :param kwargs: any keywords passed that we ignore.
        """
        self.org_id = str(org_id)
        self.endpoint = user_management_endpoint
        self.test_mode = test_mode
        self.logger = logger
        self.retry_max_attempts = retry_max_attempts
        self.retry_first_delay = retry_first_delay
        self.retry_random_delay = retry_random_delay
        self.timeout = float(timeout_seconds) if timeout_seconds and float(timeout_seconds) > 0.0 else None
        self.throttle_actions = max(int(throttle_actions), 1)
        self.throttle_commands = max(int(throttle_commands), 1)
        self.action_queue = []
        self.local_status = {"multiple-query-count": 0,
                             "single-query-count": 0,
                             "actions-sent": 0,
                             "actions-completed": 0,
                             "actions-queued": 0}
        self.server_status = {"status": "Never contacted",
                              "endpoint": self.endpoint}
        if auth:
            self.auth = auth
        elif auth_dict:
            self.auth = self._get_auth(ims_host=ims_host, ims_endpoint_jwt=ims_endpoint_jwt, **auth_dict)
        else:
            raise ValueError("Connector create: either auth (an Auth object) or auth_dict (a dictionary) is required")
        self.session = requests.Session()
        ua_string = "umapi-client/" + umapi_version + " Python/" + python_version() + " (" + platform_version() + ")"
        if user_agent and user_agent.strip():
            ua_string = user_agent.strip() + " " + ua_string
        self.session.headers["User-Agent"] = ua_string

    def _get_auth(self, ims_host, ims_endpoint_jwt,
                  tech_acct_id=None, api_key=None, client_secret=None,
                  private_key_file=None, private_key_data=None,
                  **kwargs):
        tech_acct_id = tech_acct_id or kwargs.get("tech_acct")
        private_key_file = private_key_file or kwargs.get("priv_key_path")
        if not (tech_acct_id and api_key and client_secret and (private_key_data or private_key_file)):
            raise ValueError("Connector create: not all required auth parameters were supplied; please see docs")
        if private_key_data:
            jwt = JWT(self.org_id, tech_acct_id, ims_host, api_key, six.StringIO(private_key_data))
        else:
            with open(private_key_file, 'r') as private_key_stream:
                jwt = JWT(self.org_id, tech_acct_id, ims_host, api_key, private_key_stream)
        token = AccessRequest("https://" + ims_host + ims_endpoint_jwt, api_key, client_secret, jwt())
        return Auth(api_key, token())

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
                result = self.session.get(components[0] + "://" + components[1] + "/status", timeout=self.timeout)
            except Exception as e:
                if self.logger: self.logger.debug("Failed to connect to server for status: %s", e)
                result = None
            if result and result.status_code == 200:
                self.server_status = result.json()
                self.server_status["endpoint"] = self.endpoint
            elif result:
                if self.logger: self.logger.debug("Server status response not understandable: Status: %d, Body: %s",
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
            query_path += "/" + urlparse.quote(component)
        if query_params: query_path += "?" + urlparse.urlencode(query_params)
        try:
            result = self.make_call(query_path)
            body = result.json()
        except RequestError as re:
            if re.result.status_code == 404:
                if self.logger: self.logger.debug("Ran %s query: %s %s (0 found)",
                                                  object_type, url_params, query_params)
                return {}
            else:
                raise re
        if body.get("result") == "success":
            value = body.get(object_type, {})
            if self.logger: self.logger.debug("Ran %s query: %s %s (1 found)", object_type, url_params, query_params)
            return value
        else:
            raise ClientError("OK status but no 'success' result", result)

    def query_multiple(self, object_type, page=0, url_params=None, query_params=None):
        # type: (str, int, list, dict) -> tuple
        """
        Query for a page of objects.  Defaults to the (0-based) first page.
        Sadly, the sort order is undetermined.
        :param object_type: string query type (e.g., "users" or "groups")
        :param page: numeric page (0-based) of results to get (up to 200 in a page)
        :param url_params: optional list of strings to provide as additional URL components
        :param query_params: optional dictionary of query options
        :return: tuple (list of returned dictionaries (one for each query result), bool for whether this is last page)
        """
        # Server API convention (v2) is that the pluralized object type goes into the endpoint
        # and is also the key in the response dictionary for the returned objects.
        self.local_status["multiple-query-count"] += 1
        query_type = object_type + "s"  # poor man's plural
        query_path = "/{}/{}/{:d}".format(query_type, self.org_id, page)
        for component in url_params if url_params else []:
            query_path += "/" + urlparse.quote(component)
        if query_params: query_path += "?" + urlparse.urlencode(query_params)
        try:
            result = self.make_call(query_path)
            body = result.json()
        except RequestError as re:
            if re.result.status_code == 404:
                if self.logger: self.logger.debug("Ran %s query: %s %s (0 found)",
                                                  object_type, url_params, query_params)
                return [], True
            else:
                raise re
        if body.get("result") == "success":
            values = body.get(query_type, [])
            last_page = body.get("lastPage", False)
            if self.logger: self.logger.debug("Ran multi-%s query: %s %s (page %d: %d found)",
                                              object_type, url_params, query_params, page, len(values))
            return values, last_page
        else:
            raise ClientError("OK status but no 'success' result", result)

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
        you can set immeediate=False which will cause the connection to wait
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
        split_actions = []
        exceptions = []
        for a in actions:
            if len(a.commands) == 0:
                if self.logger: self.logger.warning("Sending action with no commands: %s", a.frame)
            if len(a.commands) > self.throttle_commands:
                if self.logger: self.logger.debug("Throttling action %s to have a maximum of %d commands.",
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
            if self.logger: self.logger.debug("Executing %d actions (%d remaining).", len(batch), len(actions))
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
                if self.logger: self.logger.warning("Server action result: no errors, but no success:\n%s", body)
            return len(actions)
        try:
            if body.get("result") == "success":
                if self.logger: self.logger.warning("Server action result: errors, but success report:\n%s", body)
            for error in body["errors"]:
                actions[error["index"]].report_command_error(error)
        except:
            raise ClientError(str(body), result)
        return body.get("completed", 0)

    def make_call(self, path, body=None):
        """
        Make a single UMAPI call with error handling and retry on temporary failure.
        :param path: the string endpoint path for the call
        :param body: (optional) list of dictionaries to be serialized into the request body
        :return: the requests.result object (on 200 response), raise error otherwise
        """
        if body:
            request_body = json.dumps(body)

            def call():
                return self.session.post(self.endpoint + path, auth=self.auth, data=request_body, timeout=self.timeout)
        else:
            def call():
                return self.session.get(self.endpoint + path, auth=self.auth, timeout=self.timeout)

        start_time = time()
        result = None
        for num_attempts in range(1, self.retry_max_attempts + 1):
            try:
                result = call()
                if result.status_code == 200:
                    return result
                elif result.status_code in [429, 502, 503, 504]:
                    if self.logger: self.logger.warning("UMAPI timeout...service unavailable (code %d on try %d)",
                                                        result.status_code, num_attempts)
                    retry_wait = 0
                    if "Retry-After" in result.headers:
                        advice = result.headers["Retry-After"]
                        advised_time = parsedate_tz(advice)
                        if advised_time is not None:
                            # header contains date
                            retry_wait = int(mktime_tz(advised_time) - time())
                        else:
                            # header contains delta seconds
                            retry_wait = int(advice)
                    if retry_wait <= 0:
                        # use exponential back-off with random delay
                        delay = randint(0, self.retry_random_delay)
                        retry_wait = (int(pow(2, num_attempts - 1)) * self.retry_first_delay) + delay
                elif 201 <= result.status_code < 400:
                    raise ClientError("Unexpected HTTP Status {:d}: {}".format(result.status_code, result.text), result)
                elif 400 <= result.status_code < 500:
                    raise RequestError(result)
                else:
                    raise ServerError(result)
            except requests.Timeout:
                if self.logger: self.logger.warning("UMAPI connection timeout...(%d seconds on try %d)",
                                                    self.timeout, num_attempts)
                retry_wait = 0
                result = None
            if num_attempts < self.retry_max_attempts:
                if retry_wait > 0:
                    if self.logger: self.logger.warning("Next retry in %d seconds...", retry_wait)
                    sleep(retry_wait)
                else:
                    if self.logger: self.logger.warning("Immediate retry...")
        total_time = int(time() - start_time)
        if self.logger: self.logger.error("UMAPI timeout...giving up after %d attempts (%d seconds).",
                                          self.retry_max_attempts, total_time)
        raise UnavailableError(self.retry_max_attempts, total_time, result)

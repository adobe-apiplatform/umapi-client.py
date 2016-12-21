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
import logging
from email.utils import parsedate_tz, mktime_tz
from random import randint
from time import time, sleep

import requests
import six.moves.urllib.parse as urlparse

from .auth import JWT, Auth, AccessRequest
from .error import TimeoutError, ClientError, RequestError, ServerError


class Connection:
    """
    An org-specific, authorized connection to the UMAPI service.  Each method
    makes a single call on the endpoint and returns the result (or raises an error).
    """
    def __init__(self,
                 org_id, tech_acct_id, api_key, client_secret, private_key_file,
                 ims_host='ims-na1.adobelogin.com',
                 ims_endpoint_jwt='/ims/exchange/jwt/',
                 user_management_endpoint='https://usermanagement.adobe.io/v2/usermanagement',
                 test_mode=False,
                 logger=logging.getLogger("umapi_client"),
                 retry_max_attempts=4,
                 retry_first_delay=15,
                 retry_random_delay=5,
                 **kwargs):
        """
        Open a connection for the given parameters that has the given options.
        The connection is authorized and the auth token reused on all calls.

        Required organizational parameters:
        :param org_id: string OrganizationID from Adobe.IO integration data
        :param tech_acct_id: string technical account ID from Adobe.IO integration data
        :param api_key: string api_key from Adobe.IO integration data
        :param client_secret: string client secret from Adobe.IO integration data
        :param private_key_file: path to local private key file that matches Adobe.IO public key for integration

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

        Additional keywords are allowed to make it easy to pass in a dictionary.
        :param kwargs:
        """
        self.org_id = org_id
        self.endpoint = user_management_endpoint
        self.test_mode = test_mode
        self.logger = logger
        self.retry_max_attempts = retry_max_attempts
        self.retry_first_delay = retry_first_delay
        self.retry_random_delay = retry_random_delay
        with open(private_key_file, 'r') as private_key_stream:
            jwt = JWT(self.org_id, tech_acct_id, ims_host, api_key, private_key_stream)
        token = AccessRequest("https://" + ims_host + ims_endpoint_jwt, api_key, client_secret, jwt())
        self.auth = Auth(api_key, token())

    def query_single(self, object_type, url_params, query_params={}):
        """
        Query for a single object.
        :param object_type: string query type (e.g., "users" or "groups")
        :param url_params: required list of strings to provide as additional URL components
        :param query_params: optional dictionary of query options
        :return: the found object (a dictionary), which is empty if none were found
        """
        # Server API convention (v2) is that the pluralized object type goes into the endpoint
        # but the object type is the key in the response dictionary for the returned object.
        query_type = object_type + "s"  # poor man's plural
        query_path = "/{}/{}".format(query_type, self.org_id)
        for component in url_params:
            query_path += "/" + urlparse.quote(component)
        if query_params: query_path += "?" + urlparse.urlencode(query_params)
        try:
            body = self.make_call(query_path)
        except RequestError as re:
            if re.result.status_code == 404:
                if self.logger: self.logger.debug("Ran {} query: {} {} (0 found)",
                                                  object_type, url_params, query_params)
                return {}
            else:
                raise re
        if body.get("result") == "success":
            value = body.get(object_type, {})
            if self.logger: self.logger.debug("Ran {} query: {} {} (1 found)", object_type, url_params, query_params)
            return value
        else:
            raise ClientError(body)

    def query_multiple(self, object_type, page=0, url_params=[], query_params={}):
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
        query_type = object_type + "s"  # poor man's plural
        query_path = "/{}/{}/{:d}".format(query_type, self.org_id, page)
        for component in url_params:
            query_path += "/" + urlparse.quote(component)
        if query_params: query_path += "?" + urlparse.urlencode(query_params)
        body = self.make_call(query_path)
        if body.get("result") == "success":
            values = body.get(query_type, [])
            last_page = body.get("lastPage", False)
            if self.logger: self.logger.debug("Ran multi-{} query: {} {} (page {:d}, {:d} returned)",
                                              object_type, url_params, query_params, page, len(values))
            return (values, last_page)
        else:
            raise ClientError(body)

    def execute_single(self, action):
        """
        Execute a single action (containing commands on a single object).
        :param action: the Action to be executed
        :return: (bool) whether the execution was successful
        """
        return self.execute_multiple([action]) == 1

    def execute_multiple(self, actions):
        """
        Execute multiple Actions (each containing commands on a single object).
        For each action that has a problem, we annotate the action with the
        error information for that action, and we return the number of
        successful actions.
        :param actions: the list of Action objects to be executed
        :return: count of successful actions
        """
        wire_form = [a.wire_dict() for a in actions]
        if self.test_mode:
            body = self.make_call("/actions/%s?testOnly=true" % self.org_id, wire_form).json()
        else:
            body = self.make_call("/actions/%s" % self.org_id, wire_form)
        if body.get("result") == "success":
            return len(actions)
        try:
            for error in body["errors"]:
                actions[error["index"]].report_error(error)
        except:
            raise ClientError(body)
        return body.get("completed", 0)

    def make_call(self, path, body=None):
        """
        Make a single UMAPI call with error handling and retry on temporary failure.
        :param path: the string endpoint path for the call
        :param body: (optional) list of dictionaries to be serialized into the request body
        :return: result body from the call
        """
        if body:
            request_body = json.dumps(body)
            def call(): return requests.post(self.endpoint + path, auth=self.auth, data=request_body)
        else:
            def call(): return requests.get(self.endpoint + path, auth=self.auth)

        total_time = wait_time = 0
        for num_attempts in range(1, self.retry_max_attempts + 1):
            if wait_time > 0:
                sleep(wait_time)
                total_time += wait_time
                wait_time = 0
            result = call()
            if result.status_code == 200:
                return result.json()
            elif result.status_code in [429, 502, 503, 504]:
                if self.logger: self.logger.warning("UMAPI timeout...service unavailable (code {:d} on try {:d})",
                                                    result.status_code, num_attempts)
                if "Retry-After" in result.headers:
                    advice = result.headers["Retry-After"]
                    advised_time = parsedate_tz(advice)
                    if advised_time is not None:
                        # header contains date
                        wait_time = int(mktime_tz(advised_time) - time())
                    else:
                        # header contains delta seconds
                        wait_time = int(advice)
                if wait_time <= 0:
                    # use exponential back-off with random delay
                    delay = randint(0, self.retry_random_delay)
                    wait_time = (int(pow(2, num_attempts)) * self.retry_first_delay) + delay
                if self.logger: self.logger.warning("Next retry in %d seconds...", wait_time)
            elif 400 <= result.status_code < 500:
                raise RequestError(result)
            else:
                raise ServerError(result)
        if self.logger: self.logger.error("UMAPI timeout...giving up after %d attempts.", self.retry_max_attempts)
        raise TimeoutError(self.retry_max_attempts, total_time)

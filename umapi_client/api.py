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

import re

import six

from .connection import Connection


class Action:
    """
    An sequence of commands for the API to perform on a single object.
    """

    def __init__(self, **kwargs):
        """
        Create an Action.  You must specify the object that the action applies to.

        The Action keeps track of its commands and also any errors that arise
        in execution of those commands.
        :param kwargs: key/value pairs that identify the object being updated
        """
        self.frame = dict(kwargs)
        self.commands = []
        self.errors = []

    def wire_dict(self):
        """
        The dictionary that should be sent (in JSON form) to the server for this action.
        :return: dictionary
        """
        return dict(self.frame, do=self.commands)

    def do(self, **kwargs):
        """
        Add commands to the sequence.

        Be careful: because this runs in Python 2.x, the order
        of the kwargs dict may not match the order in which the args were specified.  Thus,
        if you care about specific ordering, you must make multiple calls to do in that order.
        Luckily, do returns the Action so you can compose easily: Action(...).do(...).do(...).
        See also do_first, below.
        :param kwargs: the key/value pairs to add
        :return: the action
        """
        for k, v in six.iteritems(kwargs):
            self.commands.append({k: v})
        return self

    def do_first(self, **kwargs):
        """
        Insert commands at the front of the sequence.

        This is provided because certain commands
        have to come first (such as user creation), but may be added after other commands.
        Later calls to do_first put their commands before those in the earlier calls.

        Also, since the order of iterated kwargs is not guaranteed (in Python 2.x),
        you should really only call do_first with one keyword at a time.  See the doc of do
        for more details.
        :param kwargs: the key/value pair to do first
        :return: the action, so you can do Action(...).do_first(...).do(...)
        """
        for k, v in six.iteritems(kwargs):
            self.commands.insert(0, {k: v})
        return self

    def report_command_error(self, error_dict):
        """
        Report a server error executing a command.

        We keep track of the command's position in the command list,
        and we add annotation of what the command was, to the error.
        :param error_dict: The server's error dict for the error encountered
        """
        error = dict(error_dict)
        error["command"] = self.commands[error_dict["step"]]
        del error["index"]  # doesn't matter which action this was in the server-sent batch
        self.errors.append(error)

    def execution_errors(self):
        """
        Return a list of commands that encountered execution errors, with the error.

        Each dictionary entry gives the command dictionary and the error dictionary
        :return: list of commands that gave errors, with their error information
        """
        return [dict(e) for e in self.errors]


class UserAction(Action):
    """
    An sequence of commands for the UMAPI to perform on a single user.
    """

    def __init__(self, email=None, username=None, domain=None, **kwargs):
        """
        Create an Action for a user identified either by email or by username and domain.
        There is never a reason to specify both email and username.
        :param username: string, username in the Adobe domain (might be email)
        :param domain: string, required if the username is not an email address
        :param kwargs: other key/value pairs desired to identify this user
        """
        if email:
            if username or domain:
                ValueError("User create: Email was specified; don't also specify username or domain")
            if not re.match(r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~;-]+([.][a-zA-Z0-9!#$%&'*+/=?^_`{|}~;-]+)*"
                            r"@"
                            r"[a-zA-Z0-9-]+([.][a-zA-Z0-9-]+)+$", email):
                ValueError("Action create: Illegal email format")
            Action.__init__(user=email, **kwargs)
        else:
            if not username or not domain:
                ValueError("User create: Both username and domain must be specified")
            if not re.match(r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~;-]+([.][a-zA-Z0-9!#$%&'*+/=?^_`{|}~;-]+)*$", username):
                ValueError("User create: Illegal characters in username")
            if not re.match(r"^[a-zA-Z0-9-]+([.][a-zA-Z0-9-]+)+$", domain):
                ValueError("User create: Illegal domain format")
            Action.__init__(user=username, domain=domain, **kwargs)


class QueryMultiple:
    """
    A QueryMultiple runs a query against a connection.  The results can be iterated or fetched in bulk.
    """

    def __init__(self, connection, object_type, url_params=None, query_params=None):
        # type: (Connection, str, list, dict)
        """
        Provide the connection and query parameters when you create the query.

        :param connection: The Connection to run the query against
        :param object_type: The type of object being queried (e.g., "user" or "group")
        :param url_params: Query qualifiers that go in the URL path (e.g., a group name when querying users)
        :param query_params: Query qualifiers that go in the query string (e.g., a domain name)
        """
        self.conn = connection
        self.object_type = object_type
        self.url_params = url_params if url_params else []
        self.query_params = query_params if query_params else {}
        self.reload()

    # noinspection PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit
    def reload(self):
        """
        Rerun the query (lazily).
        The results will contain any values on the server side that have changed since the last run.
        :return: None
        """
        self._results = []
        self._next_item_index = 0
        self._next_page_index = 0
        self._last_page_seen = False

    def _next_page(self):
        """
        Fetch the next page of the query.
        """
        if self._last_page_seen: return 0
        new, self._last_page_seen = self.conn.query_multiple(self.object_type, self._next_page_index,
                                                             self.url_params, self.query_params)
        self._next_page_index += 1
        if len(new) == 0:
            self._last_page_seen = True  # don't bother with next page if nothing was returned
        else:
            self._results += new

    def _next_item(self):
        while self._next_item_index >= len(self._results):
            if self._last_page_seen:
                raise StopIteration
            self._next_page()
        value = self._results[self._next_item_index]
        self._next_item_index += 1
        return value

    class _QueryIterator:
        def __init__(self, query):
            self.query = query

        # noinspection PyProtectedMember
        def next(self):
            return self.query._next_item()

    def __iter__(self):
        return self._QueryIterator(self)

    def all_results(self):
        """
        Eagerly fetch all the results.
        This can be called after already doing some amount of iteration, and it will return
        all the previously-iterated results as well as any results that weren't yet iterated.
        :return: a list of all the results.
        """
        while not self._last_page_seen:
            self._next_page()
        return list(self._results)


class UsersQuery(QueryMultiple):
    """
    Query for users meeting (optional) criteria
    """

    def __init__(self, connection, in_group="", in_domain=""):
        """
        Create a query for all users, or for those in a group or domain or both
        :param connection: Connection to run the query against
        :param in_group: (optional) name of the group to restrict the query to
        :param in_domain: (optional) name of the domain to restrict the query to
        """
        groups = [in_group] if in_group else []
        domains = {"domain": in_domain} if in_domain else {}
        QueryMultiple.__init__(self, connection=connection, object_type="user", url_params=groups, query_params=domains)


class GroupsQuery(QueryMultiple):
    """
    Query for all groups
    """

    def __init__(self, connection):
        """
        Create a query for all groups
        :param connection: Connection to run the query against
        """
        QueryMultiple.__init__(self, connection=connection, object_type="group")

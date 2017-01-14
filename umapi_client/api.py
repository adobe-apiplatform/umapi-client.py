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
        self.split_actions = None

    def split(self, max_commands):
        """
        Split this action into an equivalent list of actions, each of which have at most max_commands commands.
        :param max_commands: max number of commands allowed in any action
        :return: the list of commands created from this one
        """
        a_prior = Action(**self.frame)
        a_prior.commands = list(self.commands)
        self.split_actions = [a_prior]
        while len(a_prior.commands) > max_commands:
            a_next = Action(**self.frame)
            a_prior.commands, a_next.commands = a_prior.commands[0:max_commands], a_prior.commands[max_commands:]
            self.split_actions.append(a_next)
            a_prior = a_next
        return self.split_actions

    def wire_dict(self):
        """
        The dictionary that should be sent (in JSON form) to the server for this action.
        :return: dictionary
        """
        return dict(self.frame, do=self.commands)

    def append(self, **kwargs):
        """
        Add commands at the end of the sequence.

        Be careful: because this runs in Python 2.x, the order of the kwargs dict may not match
        the order in which the args were specified.  Thus, if you care about specific ordering,
        you must make multiple calls to append in that order.  Luckily, append returns
        the Action so you can compose easily: Action(...).append(...).append(...).
        See also insert, below.
        :param kwargs: the key/value pairs to add
        :return: the action
        """
        for k, v in six.iteritems(kwargs):
            self.commands.append({k: v})
        return self

    def insert(self, **kwargs):
        """
        Insert commands at the beginning of the sequence.

        This is provided because certain commands
        have to come first (such as user creation), but may be need to beadded
        after other commands have already been specified.
        Later calls to insert put their commands before those in the earlier calls.

        Also, since the order of iterated kwargs is not guaranteed (in Python 2.x),
        you should really only call insert with one keyword at a time.  See the doc of append
        for more details.
        :param kwargs: the key/value pair to append first
        :return: the action, so you can append Action(...).insert(...).append(...)
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
        error["target"] = self.frame
        del error["index"]  # throttling can change which action this was in the batch
        del error["step"]   # throttling can change which step this was in the action
        self.errors.append(error)

    def execution_errors(self):
        """
        Return a list of commands that encountered execution errors, with the error.

        Each dictionary entry gives the command dictionary and the error dictionary
        :return: list of commands that gave errors, with their error information
        """
        if self.split_actions:
            # throttling split this action, get errors from the split
            return [dict(e) for s in self.split_actions for e in s.errors]
        else:
            return [dict(e) for e in self.errors]


class QueryMultiple:
    """
    A QueryMultiple runs a query against a connection.  The results can be iterated or fetched in bulk.
    """
    def __init__(self, connection, object_type, url_params=None, query_params=None):
        # type: (Connection, str, list, dict) -> None
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
        self._results = []
        self._next_item_index = 0
        self._next_page_index = 0
        self._last_page_seen = False

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
        if self._last_page_seen:
            raise StopIteration
        new, self._last_page_seen = self.conn.query_multiple(self.object_type, self._next_page_index,
                                                             self.url_params, self.query_params)
        self._next_page_index += 1
        if len(new) == 0:
            self._last_page_seen = True  # don't bother with next page if nothing was returned
        else:
            self._results += new

    def _next_item(self):
        while self._next_item_index >= len(self._results):
            self._next_page()
        value = self._results[self._next_item_index]
        self._next_item_index += 1
        return value

    class _QueryIterator:
        def __init__(self, query):
            self.query = query

        def __iter__(self):
            """In python3, the iterator object must have an __iter__ method which returns the iterator"""
            return self

        # noinspection PyProtectedMember
        def next(self):
            """In python2, this is the "get next" method required by the interactor protocol"""
            return self.query._next_item()

        def __next__(self):
            """In python3, this is the "get next" method required by the interactor protocol"""
            return self.next()

    def __iter__(self):
        """Asking for a new iterator causes the query to reload."""
        self.reload()
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
        self._next_item_index = len(self._results)
        return list(self._results)


class QuerySingle:
    """
    Look for a single object
    """
    def __init__(self, connection, object_type, url_params=None, query_params=None):
        # type: (Connection, str, list, dict) -> None
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
        self._result = None

    def reload(self):
        """
        Rerun the query (lazily).
        The result will contain a value on the server side that have changed since the last run.
        :return: None
        """
        self._result = None

    def _fetch_result(self):
        """
        Fetch the queried object.
        """
        self._result = self.conn.query_single(self.object_type, self.url_params, self.query_params)

    def result(self):
        """
        Fetch the result, if we haven't already or if reload has been called.
        :return: the result object of the query.
        """
        if self._result is None:
            self._fetch_result()
        return self._result

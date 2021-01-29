# Copyright (c) 2016-2017 Adobe Inc.  All rights reserved.
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
Set up for testing
"""

import logging

import pytest
from io import StringIO

mock_connection_params = {
    "org_id": "N/A",
    "auth": "N/A",
    "user_management_endpoint": 'https://test/',
    "logger": None,
    "retry_max_attempts": 3,
    "retry_first_delay": 1,
    "retry_random_delay": 2,
}


class MockResponse:
    def __init__(self, status=200, body=None, headers=None, text=None):
        self.status_code = status
        self.body = body if body is not None else {}
        self.headers = headers if headers else {}
        self.text = text if text else ""

    def json(self):
        return self.body


# py.test doesn't divert string logging, so use it
@pytest.fixture
def log_stream():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    yield stream, logger
    handler.close()

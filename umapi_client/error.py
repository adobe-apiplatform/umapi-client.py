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


class UnavailableError(Exception):
    def __init__(self, attempts, seconds, result):
        Exception.__init__(self, "Server unavailable: Made {:d} attempts over {:d} seconds".format(attempts, seconds))
        self.attempts = attempts
        self.seconds = seconds
        self.result = result


class ServerError(Exception):
    def __init__(self, result):
        Exception.__init__(self, "Server error: " + result.text)
        self.result = result


class RequestError(Exception):
    def __init__(self, result):
        Exception.__init__(self, "Request Error: " + result.text)
        self.result = result


class ClientError(Exception):
    def __init__(self, message, result):
        Exception.__init__(self, "Server response not understood: " + message)
        self.result = result

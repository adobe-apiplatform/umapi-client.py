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

import requests
import json
import six
from .error import UMAPIError, UMAPIRetryError, UMAPIRequestError, ActionFormatError


class UMAPI(object):
    def __init__(self, endpoint, auth, test_mode=False):
        self.endpoint = str(endpoint)
        self.auth = auth
        self.test_mode = test_mode

    def users(self, org_id, page=0):
        return self._call('/users/%s/%d' % (org_id, page), requests.get)

    def groups(self, org_id, page=0):
        return self._call('/groups/%s/%d' % (org_id, page), requests.get)

    def action(self, org_id, action):
        if not isinstance(action, Action):
            if not isinstance(action, str) and (hasattr(action, "__getitem__") or hasattr(action, "__iter__")):
                actions = [a.data for a in action]
            else:
                raise ActionFormatError("action must be iterable, indexable or Action object")
        else:
            actions = [action.data]
        if self.test_mode:
            return self._call('/action/%s?testOnly=true' % org_id, requests.post, actions)
        else:
            return self._call('/action/%s' % org_id, requests.post, actions)

    def _call(self, method, call, params=None):
        data = ''
        if params:
            data = json.dumps(params)
        res = call(self.endpoint+method, data=data, auth=self.auth)
        if res.status_code == 200:
            result = res.json()
            if "result" in result:
                if result["result"] == "error":
                    raise UMAPIRequestError(result["errors"][0]["errorCode"])
                else:
                    return result
            else:
                raise UMAPIRequestError("Request Error -- Unknown Result Status")
        if res.status_code in [429, 502, 503, 504]:
            raise UMAPIRetryError(res)
        else:
            raise UMAPIError(res)


class Action(object):
    def __init__(self, user_key, **kwargs):
        self.data = {"user": user_key, "do": []}    # empty actions upon creation
        for k, v in six.iteritems(kwargs):
            self.data[k] = v

    # do adds to any existing actions, so can you Action(...).do(...).do(...)
    def do(self, **kwargs):
        # add "create" / "add" / "removeFrom" first
        for k, v in list(six.iteritems(kwargs)):
            if k.startswith("create") or k.startswith("addAdobe") or k.startswith("removeFrom"):
                self.data["do"].append({k: v})
                del kwargs[k]

        # now do the other actions, in a canonical order (to avoid implementation variations)
        for k, v in sorted(six.iteritems(kwargs)):
            if k in ['add', 'remove']:
                self.data["do"].append({k: {"product": v}})
            else:
                self.data["do"].append({k: v})
        return self

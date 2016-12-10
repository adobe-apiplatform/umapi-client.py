import requests
import json
from error import UMAPIError, UMAPIRetryError, UMAPIRequestError, ActionFormatError


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
            if not isinstance(action, str) and hasattr(action, "__getitem__") or hasattr(action, "__iter__"):
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
    def __init__(self, user_key, *args, **kwargs):
        self.data = {"user": user_key, "do": []}    # empty actions upon creation
        for k, v in kwargs.items():
            self.data[k] = v

    # do adds to any existing actions, so can you Action(...).do(...).do(...)
    def do(self, *args, **kwargs):
        # add "create" / "add" / "removeFrom" first
        for k, v in kwargs.items():
            if k.startswith("create") or k.startswith("addAdobe") or k.startswith("removeFrom"):
                self.data["do"].append({k: v})
                del kwargs[k]

        # now do the other actions
        for k, v in kwargs.items():
            if k in ['add', 'remove']:
                self.data["do"].append({k: {"product": v}})
            else:
                self.data["do"].append({k: v})
        return self

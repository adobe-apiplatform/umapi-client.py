import requests
import json
from error import UMAPIError, UMAPIRetryError, ActionFormatError


class UMAPI(object):
    def __init__(self, endpoint, auth):
        self.endpoint = str(endpoint)
        self.auth = auth

    def users(self, org_id, page=0):
        return self._call('/users/%s/%d' % (org_id, page), requests.get)

    def groups(self, org_id, page=0):
        return self._call('/groups/%s/%d' % (org_id, page), requests.get)

    def action(self, org_id, action):
        if not isinstance(action, Action):
            if hasattr(action, "__getitem__") or hasattr(action, "__iter__"):
                actions = [a.data for a in action]
            else:
                raise ActionFormatError("action must be iterable, indexable or Action object")
        else:
            actions = [action.data]
        return self._call('/action/%s' % org_id, requests.post, actions)

    def _call(self, method, call, params=None):
        data = ''
        if params:
            data = json.dumps(params)
        res = call(self.endpoint+method, data=data, auth=self.auth)
        if res.status_code == 200:
            return res.json()
        if res.status_code in [429, 502, 503, 504]:
            raise UMAPIRetryError(res)
        else:
            raise UMAPIError(res)


class Action(object):
    def __init__(self, user):
        self.data = {"user": user}

    def do(self, *args, **kwargs):
        self.data["do"] = []
        # add "create" first
        for k, v in kwargs.items():
            if k.startswith("create"):
                self.data["do"].append({k: v})
                del kwargs[k]

        # now do the other actions
        for k, v in kwargs.items():
            if k in ['add', 'remove']:
                self.data["do"].append({k: {"product": v}})
            else:
                self.data["do"].append({k: v})
        return self

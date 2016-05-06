import requests
import json
from error import UMAPIError, UMAPIRetryError


class UMAPI(object):
    def __init__(self, endpoint, auth):
        self.endpoint = endpoint
        self.auth = auth

    def users(self, org_id, page):
        return self._call('/users/%s/%d' % (org_id, page), requests.get)

    def _call(self, method, call, params={}):
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

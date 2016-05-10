import requests
import json
from error import UMAPIError, UMAPIRetryError


class UMAPI(object):
    def __init__(self, endpoint, auth):
        self.endpoint = str(endpoint)
        self.auth = auth

    def users(self, org_id, page=0):
        return self._call('/users/%s/%d' % (org_id, page), requests.get)

    def groups(self, org_id, page=0):
        return self._call('/groups/%s/%d' % (org_id, page), requests.get)

    def user_create(self, org_id, user_id, usertype="AdobeID", attr={}):
        if not attr:
            attr = {"email": user_id}
        params = {
            "user": user_id,
            "do": [
                {
                    "create" + usertype: attr,
                }
            ]
        }
        return self._call('/action/%s' % org_id, requests.post, params)

    def product_add(self, org_id, user_id, prods):
        params = {
            "user": user_id,
            "do": [
                {
                    "add": {
                        "product": prods
                    }
                }
            ]
        }
        return self._call('/action/%s' % org_id, requests.post, params)

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

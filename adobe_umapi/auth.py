import time
# noinspection PyPackageRequirements
import jwt      # package name is PyJWT in setup
import requests
import datetime as dt
from urllib import urlencode


class JWT(object):
    def __init__(self, org_id, tech_acct, ims_host, api_key, key_file):
        self.expiry_time = int(time.time()) + 60*60*24
        self.org_id = org_id
        self.tech_acct = tech_acct
        self.ims_host = ims_host
        self.api_key = api_key

        self.key = key_file.read()
        key_file.close()

    def __call__(self):
        payload = {
            "exp": self.expiry_time,
            "iss": self.org_id,
            "sub": self.tech_acct,
            "aud": "https://" + self.ims_host + "/c/" + self.api_key,
            "https://" + self.ims_host + "/s/" + "ent_user_sdk": True
        }

        # create JSON Web Token
        # noinspection PyUnresolvedReferences
        jwt_token = jwt.encode(payload, self.key, algorithm='RS256')
        # decode bytes into string
        return jwt_token.decode("utf-8")


class AccessRequest(object):
    def __init__(self, endpoint, api_key, client_secret, jwt_token):
        self.endpoint = endpoint
        self.api_key = api_key
        self.client_secret = client_secret
        self.jwt_token = jwt_token
        self.expiry = None

    def __call__(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }
        body = urlencode({
            "client_id": self.api_key,
            "client_secret": self.client_secret,
            "jwt_token": self.jwt_token
        })

        res = requests.post(self.endpoint, headers=headers, data=body)
        if res.status_code != 200:
            raise Exception("Access Request Error (%s) [Text: %s, Headers: %s]" % (res.status_code,
                                                                                   res.text, res.headers))

        self.set_expiry(res.json()['expires_in'])

        return res.json()['access_token']

    def set_expiry(self, expires_in):
        expires_in = int(round(expires_in/1000))
        self.expiry = dt.datetime.now() + dt.timedelta(seconds=expires_in)


# noinspection PyUnresolvedReferences
class Auth(requests.auth.AuthBase):
    def __init__(self, api_key, access_token):
        self.api_key = api_key
        self.access_token = access_token

    def __call__(self, r):
        r.headers['Content-type'] = 'application/json'
        r.headers['Accept'] = 'application/json'
        r.headers['x-api-key'] = self.api_key
        r.headers['Authorization'] = 'Bearer ' + self.access_token
        return r

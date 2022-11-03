# Copyright (c) 2016-2021 Adobe Inc.  All rights reserved.
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

import datetime as dt
import time

import jwt
import requests
import urllib.parse as urlparse
import logging

logger = logging.getLogger(__name__)


class AdobeAuthBase(requests.auth.AuthBase):
    def __init__(self, client_id, client_secret, auth_host, auth_endpoint,
                 ssl_verify):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_host = auth_host
        self.auth_endpoint = auth_endpoint
        self.ssl_verify = ssl_verify
        self.expiry = None
        self.token = None

    def set_expiry(self, expires_in):
        expires_in = int(round(expires_in/1000))
        self.expiry = dt.datetime.now() + dt.timedelta(seconds=expires_in)

    def __call__(self, r):
        if self.token is None or self.expiry is None or \
           self.expiry <= dt.datetime.now():
            self.refresh_token()
        r.headers['Content-type'] = 'application/json'
        r.headers['Accept'] = 'application/json'
        r.headers['x-api-key'] = self.client_id
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r
    
    def refresh_token(self):
        logger.info("auth token is missing or expired - refreshing now")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }

        endpoint = f"https://{self.auth_host}/{self.auth_endpoint.strip('/')}/"

        r = requests.post(endpoint, headers=headers, data=self.post_body(),
                          verify=self.ssl_verify)

        if r.status_code != 200:
            raise RuntimeError(f"Unable to authorize against {endpoint}:\n"
                               f"Response Code: {r.status_code}, Response Text: {r.text}\n"
                               f"Response Headers: {r.headers}]")

        self.set_expiry(r.json()['expires_in'])

        logger.debug("token expiration: %s", self.expiry)

        self.token = r.json()['access_token']


class OAuthS2S(AdobeAuthBase):
    def __init__(self, client_id, client_secret,
                 auth_host='ims-na1.adobelogin.com',
                 auth_endpoint='/ims/token/v2',
                 ssl_verify=True):
        logger.info("Auth type: OAuthS2S")
        super().__init__(
            client_id, client_secret, auth_host, auth_endpoint, ssl_verify
        )

    def post_body(self):
        return urlparse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "openid,AdobeID,user_management_sdk",
        })

    def set_expiry(self, expires_in):
        self.expiry = dt.datetime.now() + dt.timedelta(seconds=expires_in)


class JWTAuth(AdobeAuthBase):
    def __init__(self, org_id, client_id, client_secret, tech_acct_id,
                 priv_key_data, ssl_verify=True,
                 auth_host='ims-na1.adobelogin.com',
                 auth_endpoint='/ims/exchange/jwt/'):
        logger.info("Auth type: JWTAuth")
        self.org_id = org_id
        self.tech_acct_id = tech_acct_id
        self.priv_key_data = priv_key_data
        super().__init__(
            client_id, client_secret, auth_host, auth_endpoint, ssl_verify
        )

    def jwt_token(self):
        payload = {
            "exp": int(time.time()) + 60*60*24,
            "iss": self.org_id,
            "sub": self.tech_acct_id,
            "aud": "https://" + self.auth_host + "/c/" + self.client_id,
            "https://" + self.auth_host + "/s/" + "ent_user_sdk": True
        }

        return jwt.encode(payload, self.priv_key_data, algorithm='RS256')

    def post_body(self):
        return urlparse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "jwt_token": self.jwt_token()
        })

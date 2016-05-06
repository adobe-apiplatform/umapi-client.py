from ConfigParser import RawConfigParser
from umapi import UMAPI
from umapi.auth import JWT, AccessRequest, Auth

config = RawConfigParser()
config.read("usermanagement.config")

# server parameters
host = config.get("server", "host")
endpoint = config.get("server", "endpoint")
ims_host = config.get("server", "ims_host")
ims_endpoint_jwt = config.get("server", "ims_endpoint_jwt")

# enterprise parameters used to construct JWT
domain = config.get("enterprise", "domain")
org_id = config.get("enterprise", "org_id")
api_key = config.get("enterprise", "api_key")
client_secret = config.get("enterprise", "client_secret")
tech_acct = config.get("enterprise", "tech_acct")
priv_key_filename = config.get("enterprise", "priv_key_filename")

jwt = JWT(org_id, tech_acct, ims_host, api_key, open(priv_key_filename, 'r'))
token = AccessRequest("https://" + ims_host + ims_endpoint_jwt, api_key, client_secret, jwt())
auth = Auth(api_key, token())

api = UMAPI("https://" + host + endpoint, auth)

res = api.users(org_id, 0)
print res

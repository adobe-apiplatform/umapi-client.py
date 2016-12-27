# V2 Usage Instructions


These instructions presume you have already created your
[Adobe.IO](https://www.adobe.io/) integration, as described
in the [home page](index.html) of this documentation.

# Getting a Connection

All UMAPI access is predicated on the creation of an authenticated,
authorized connection to the UMAPI server.  This access always
happens in the context of a particular integration (as created
on adobe.io).  So it requires the following details about
your integration:

1. Organization ID
2. Tech Account ID
3. IMS Hostname
4. IMS Token Exchange Endpoint (aka JWT Endpoint)
5. API Key
6. Client Secret
7. Private Key File (unencrypted form)

Of these, the IMS Hostname and the IMS Token Exchange Endpoint
are standard across almost all integrations, so they are
built into the library as defaults and aren't typically needed.
The Tech Account ID, API Key, and Client Secret are sensitive,
as is the Private Key File, so a best practice is to keep
these values in files separate from your application.  The
Organization ID is not as sensitive, but it's best to keep
it with the others since it's also needed for authentication.

For example, suppose `config.yaml` is a YAML file
whose content contains
the sensitive data (elided here for security):

```yaml
org_id: '620049..............101@AdobeOrg'
tech_acct_id: '78E9928............A495DE3@techacct.adobe.com'
api_key: '265434.............d740ac'
client_secret: 'cc6.....-....-47b9-....-......ff3725'
private_key_file: '/path/to/my.secret.key.pem'
```

and suppose `my.secret.key.pem` contains an unencrypted
private key
like this (again, elided for security):

```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxBc5BFNUP9hdGHSuOzfxoyL2qq2qcqpSexLsefQS9fDZZjCP
...
fIOe8cq8F5Vcw6l5NwmW+Lw44hJxKAVRg+j79x6C6+zLblRhm+dHBw==
-----END RSA PRIVATE KEY-----
```

Given these two files, you can establish an authenticated,
authorized connection with code such as the following:

```python
import yaml # PyYAML from PyPI provides this module

with open(config_file_name, "r") as f:
    config = yaml.load(f)
conn = umapi_client.Connection(org_id=config["org_id"],
                               auth_dict=creds)
```

The constructor of the Connection object will do all the
work of contacting the token exchange endpoint and using
your credentials to obtain an access token, and it will
remember that access token for use with all your UMAPI
operations.  It will be called `conn` in the examples
that follow.

(If you want the details of how access token exchange
is done by the constructor, see the code or the
[v1 usage docs](usage-instructions-v1.html).)

# Querying for Users and Groups

Queries for users and groups are implemented by
classes which allow iterating the results.  These
iterators pull the results from the server in
batches of 200 or so, and cache the results locally.
You can access the full list of results with
the `all_results` method, and force the query
to be reloaded and run from the beginning again
with the `reload` method.

Each fetched user or group is represented as
a Python dictionary of its attributes.

## Get a List of Users

```python
users = QueryUsers(conn)
# print first 5 users
for i, user in enumerate(users):
    if i == 5: break
    print("User %d email: %s" % (i, user["email"]))
# get a count of all users (finishes the iteration)
user_count = len(users.all_results())
```

## Get a List of Groups

This list of groups will contain both user groups and product license
configuration groups.

```python
groups = QueryGroups(conn)
# print all the group details
for group in groups:
    print(group)
# after an hour, see if anything has changed
time.sleep(3600)
groups.reload()
for group in groups:
    print(group)
```

# Performing Operations on Users

_...under construction..._


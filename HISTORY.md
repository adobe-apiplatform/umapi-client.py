# Version 2.0

First release with functional wrapper and built-in throttling/batching.

### Version 2.0.1

Fast-follow bug fix release:

* [Issue 27](https://github.com/adobe-apiplatform/umapi-client.py/issues/27)
    * Update parameter names were incorrect.
    * Test mode wasn't working.
* [Issue 28](https://github.com/adobe-apiplatform/umapi-client.py/issues/28)
    * Reuse existing open connections across calls.

### Version 2.0.2

Enhancement release:

* [Issue 30](https://github.com/adobe-apiplatform/umapi-client.py/issues/30)
    * Add control of user-agent header.
* (No Issue)
    * Add this HISTORY.md file to summarize releases
    * Add version.py file to synchronize version between setup and module.

### Version 2.0.3

Enhancement release:

* [Issue 32](https://github.com/adobe-apiplatform/umapi-client.py/issues/32)
    * change timeout default to 2 minutes
    * add retry after timeout.
    * change default create behavior to "ignoreIfAlreadyExists"
* (No issue)
    * fix misspellings
    * change .gitignore so that .gitignore is not ignored

### Version 2.1

Server-compatibility release:

* (No Issue)
    * fix typos in docs
    * fix param documentation in functional API
    * update wire protocol for remove_from_organization with deletion of account to match server changes

### Version 2.2

Enhancement release:

* [Issue 36](https://github.com/adobe-apiplatform/umapi-client.py/issues/36)
    * catch errors during batch processing
    * return a new BatchError that has caught exceptions and batch statistics
* (No Issue)
    * allow User Sync config key names in the connection `auth_dict`

### Version 2.3

Enhancement release:

* [Issue 38](https://github.com/adobe-apiplatform/umapi-client.py/issues/38)
    * accept private_key_data instead private_key_file
    * document all accepted `auth_dict` keys
* (No Issue)
    * certify for Python 3.6

### Version 2.4

Bug fix release:

* [Issue 41](https://github.com/adobe-apiplatform/umapi-client.py/issues/41)
    * accept unicode strings from Python 2.7 clients
    * do unicode-compliant validation of usernames and email addresses

### Version 2.4.1

Bug fix release:

* [Issue 41](https://github.com/adobe-apiplatform/umapi-client.py/issues/41)
    * original fix had an overly accepting email/username validator
    * there were formatting errors in the failed validation reports

### Version 2.5

Bug fix release:

* [Issue 44](https://github.com/adobe-apiplatform/umapi-client.py/issues/44)
    * Default behavior of UsersQuery is now correct: only return direct memberships in the info about queried users.

### Version 2.5.1

Bug fix release:

* [Issue 47](https://github.com/adobe-apiplatform/umapi-client.py/issues/47)
    * When an immediate retry was done due to a timeout, there was a logging error.

### Version 2.5.2

Enhancement release:

* (No Issue)
    * Read the wall clock to return an accurate "total time" in the `UnavailableError` (and associated logging).

### Version 2.6, 2.7

Bug fix releases: The first fix attempt had problems, the second is better.

* [Issue 50](https://github.com/adobe-apiplatform/umapi-client.py/issues/50)
    * Unicode input for email produced error strings that were incorrectly encoded, so clients crashed trying to use them.

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

| tag | date | title |
|---|---|---|
| v2.0.2 | 2017-02-02 | User-Agent header enhancements |

Add a User-Agent header with version information to all server requests, and make it possible for clients to add their User-Agent info to the header.

---

| tag | date | title |
|---|---|---|
| v2.0.1 | 2017-01-17 | Release 2.0.1 with fixes for #27, #28. |

This release fixes issues discovered by user-sync development, optimizes via connection reuse, and improves the documentation around creating UserAction objects.

---

| tag | date | title |
|---|---|---|
| v2.0 | 2017-01-13 | umapi-client 2.0GM |

Public release of v2 of the umapi-client.  This release contains a functional layer and connection enhancements that completely shield the application writer from protocol issues.

You can install the release from [PyPI/umapi-client](https://pypi.python.org/pypi?:action=display&name=umapi-client&version=2.0) with `pip install --upgrade umapi-client`.

---

| tag | date | title |
|---|---|---|
| v2.0rc1 | 2017-01-05 | First release candidate for 2.0 |

Now with support for python 2.7, 3.4, 3.5, and Travis CI support/posting to PyPI.

---

| tag | date | title |
|---|---|---|
| v2.0b2 | 2016-12-27 | Release beta 2 |

With better legacy support and a brand new documentation wiki,
we are getting close to a release candidate for v2.  There's a bit
more work to do on the v2 usage docs first.

---

| tag | date | title |
|---|---|---|
| v2.0b1 | 2016-12-25 | Release 2.0b1 |

This is a massive overhaul of the v1 code.  It includes:
- better connection management.
- umapi_client automated throttling and batching of all calls, with app-level controls.
- functional wrappers for all the server API calls.
- queries that iterate
- preservation of legacy compatibility in the umap_client.legacy module.

---

| tag | date | title |
|---|---|---|
| v1.0.1 | 2016-12-17 | Release the fix of #12 |

OMG!  That has to be the shortest-lived 1.0 release ever!

This pushes the fix of #12 to PyPI.  I have also removed the older postings.

---

| tag | date | title |
|---|---|---|
| v1.0.0 | 2016-12-17 | Finally, a v1 production release! |

After many renames and typo fixes, we are finally at our v1 release.  Yay!

---

| tag | date | title |
|---|---|---|
| v1.0.0rc5 | 2016-12-17 | Updated ReadMe |

---

| tag | date | title |
|---|---|---|
| v1.0.0rc4 | 2016-12-16 | Yet another rename! |

This time to the final, Adobe-approved name, which ironically doesn't have Adobe in it!

So now we are at rc4, and I expect this will become 1.0.0 later today!  Fingers crossed!! 👍 

---

| tag | date | title |
|---|---|---|
| v1.0.0rc3 | 2016-12-14 | Copyrights added. |

Fixes #4, which was the only blocker for release.  Putting out what is hopefully the final candidate.

This also brands the adobe.io short link in the setup.py description of the module.

---

| tag | date | title |
|---|---|---|
| v1.0.0rc2 | 2016-12-14 | rename complete - next release candidate |

This is expected to be the final release, barring any bugs found in final testing.  The naming has been updated, and the build is [posted on PyPI](https://pypi.python.org/pypi/adobe-umapi-client/1.0.0rc2/).

---

| tag | date | title |
|---|---|---|
| v1.0.0rc1 | 2016-12-13 | everything done but the naming |

This was going to be the content of the first release, but then we decided to name the published object differently.  This one is functionally complete, has full smoke-testing, and runs on Python 2.7.x and 3.5.x.

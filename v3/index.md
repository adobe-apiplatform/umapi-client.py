---
layout: default
lang: en
version: v3
title: umapi-client.py - Getting Started
nav_link: Getting Started
nav_order: 10
parent: root
page_id: v3-index
---

# umapi-client.py
{:."no_toc"}

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

A Python client library for the User Management API from Adobe, aka the
[UMAPI](https://www.adobe.io/products/usermanagement/docs/gettingstarted.html).

The User Management API is an Adobe-hosted service which provides Adobe Enterprise
customers the ability to manage users programatically.  This library makes it easy
to access the UMAPI from any Python application.

> This project is open source, maintained by Adobe, and distributed under the terms
> of the OSI-approved MIT license.  Copyright (c) 2016-2022 Adobe Inc.

# Installation

## pip

The preferred way to install `umapi-client.py` is directly from the
[Python Package Index](https://pypi.org/project/umapi-client/).

```
$ pip install umapi-client
```

## wheel

The library can alternatively be installed from a wheel file or `.tar.gz` available
any [release page](https://github.com/adobe-apiplatform/umapi-client.py/releases/latest).

```
$ pip install umapi_client-x.xx-py3-none-any.whl 
```

# Getting Started

The UMAPI Client requires valid credentials. UMAPI credentials can be set up easily on the
Adobe Developer Console.

> **Note**: You must have system administrator access to your organization's Admin Console in
> order to create UMAPI credentials.

1. Log into the [Adobe Developer Console](https://developer.adobe.com/console)
2. Make sure the correct organization is selected - there is a picker in the upper-right corner of the page
3. Click “Create New Project”
4. Click “Edit Project”, give it a descriptive name
5. Click “Add API”
6. Click “Adobe Services”, “User Management API” then “Next”
7. Click “Generate Keypair” (blue button)
8. Click “Save Configured API”
9. Scroll down and you’ll see your credentials

You can alternatively supply your own keypair for Step 7. Adobe provides official documentation for this
process [here](https://developer.adobe.com/developer-console/docs/guides/authentication/JWT/JWTCertificate/).

> **Tip**: The [Adobe User Sync Tool](https://github.com/adobe-apiplatform/user-sync.py/) has a certificate
> generator built into it. It provides an easier experience than OpenSSL because it knows how to generate
> the keypair in the format required by the Developer Console. You do not have to fully configure the Sync Tool
> to use this feature. More information can be found
> [here](https://adobe-apiplatform.github.io/user-sync.py/en/user-manual/additional_tools.html#certificate-generation).

The UMAPI Client requires these credential pieces to set up a connection:

* Organization ID
* Client ID
* Client Secret
* Technical Account ID (**not** tech account email)
* Private Key File

---

**Next:** [Connection Setup](connecting.md)

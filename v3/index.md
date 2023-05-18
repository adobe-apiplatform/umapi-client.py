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

Before you can use the UMAPI client, you must set up a project in the [Adobe
Developer Console](https://developer-stage.adobe.com/console/) and add the User
Management API. This creates an integration which contains credentials used to
authenticate the client and authorize API calls.

The [Developer Console
documentation](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/implementation/)
provides a detailed guide for setting up OAuth Server-to-Server credentials.

> **Note:** JWT-based autentication is deprecated. New UMAPI integrations should
> use OAuth Server-to-Server. See
> [here](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/migration/)
> for a migration guide.

# Overview

With the integration set up, the next step is to learn how to create a UMAPI
connection and how to perform various API actions.

1. Set up authentication

   Create an `OAuthS2S` object using the credentials set up in the Adobe Developer
   Console.

2. Create connection

   Use the authentication object to establish a connection to the UMAPI.

3. Query users and groups

   Retrieve users and groups from the UMAPI using the query interface.

4. Manage users and groups

   Learn how to create actions to create new users, update users and remove
   them.

---

**Next:** [Connection Setup](connecting.md)

# Copyright (c) 2016-2017 Adobe Systems Incorporated.  All rights reserved.
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

from setuptools import setup, find_packages

version_namespace = {}
with open('umapi_client/version.py') as f:
    exec(f.read(), version_namespace)

setup(name='umapi-client',
      version=version_namespace['__version__'],
      description='Client for the User Management API (UMAPI) from Adobe - see https://adobe.ly/2h1pHgV',
      long_description=('The User Management API (aka the UMAPI) is an Adobe-hosted network service '
                        'which provides Adobe Enterprise customers the ability to manage their users.  This '
                        'client makes it easy to access the UMAPI from a local Python application.  '
                        'This client is open source, maintained by Adobe, and distributed under the terms '
                        'of the OSI-approved MIT license.  Copyright (c) 2016-2017 Adobe Systems Incorporated.'),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
      ],
      url='https://github.com/adobe-apiplatform/umapi-client.py',
      maintainer='Daniel Brotsky',
      maintainer_email='dbrotsky@adobe.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'requests>=2.4.2',
          'cryptography',
          'PyJWT',
          'six',
          'enum34'
      ],
      setup_requires=[
          'pytest-runner',
      ],
      tests_require=[
          'pytest>=3.0.5',
          'mock',
          'PyYAML',
      ],
      zip_safe=False)

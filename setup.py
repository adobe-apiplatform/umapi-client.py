from setuptools import setup, find_packages


setup(name='adobe-umapi-client',
      version='1.0.0rc2',
      description='Adobe User Management API (UMAPI) client - see http://bit.ly/2hwkVrs',
      long_description=('The Adobe User Management API (aka the Adobe UMAPI) is an Adobe-hosted network service '
                        'which provides Adobe Enterprise customers the ability to manage their users.  This '
                        'client makes it easy to access the Adobe UMAPI from a local Python application.  '
                        'This client is open source, maintained by Adobe, and distributed under the terms '
                        'of the OSI-approved MIT license.  Copyright (c) 2016 Adobe Systems Incorporated.'),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
      ],
      url='https://github.com/adobe-apiplatform/adobe-umapi-client.py',
      maintainer='Daniel Brotsky',
      maintainer_email='dbrotsky@adobe.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
        'requests',
        'cryptography',
        'PyJWT',
        'six',
      ],
      setup_requires=[
        'pytest-runner',
      ],
      tests_require=[
        'pytest',
        'mock',
      ],
      zip_safe=False)

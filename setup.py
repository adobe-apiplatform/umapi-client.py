from setuptools import setup, find_packages


setup(name='adobe-umapi',
      version='1.0.0',
      description='Adobe UMAPI client - see http://bit.ly/2hwkVrs',
      url='https://github.com/adobe-apiplatform/adobe-umapi.py',
      author='Daniel Brotsky',
      author_email='dbrotsky@adobe.com',
      license='Copyright (c) 2016 Adobe Systems Incorporated.  All rights reserved.',
      packages=find_packages(),
      install_requires=[
        'requests',
        'cryptography',
        'PyJWT', 'jwt',
      ],
      setup_requires=[
        'pytest-runner',
      ],
      tests_require=[
        'pytest',
        'mock',
      ],
      zip_safe=False)

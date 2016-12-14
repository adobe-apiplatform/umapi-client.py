from setuptools import setup, find_packages


setup(name='adobe-umapi',
      version='1.0.0rc1',
      description='Adobe User Management API (UMAPI) client - see http://bit.ly/2hwkVrs',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
      ],
      url='https://github.com/adobe-apiplatform/adobe-umapi.py',
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

from setuptools import setup


setup(name='umapi',
      version='0.9.0',
      description='Adobe User Management API Interfaces',
      url='git@git.corp.adobe.com:adorton/cce-umapi.git',
      author='Andrew Dorton',
      author_email='adorton@adobe.com',
      license='Copyright Adobe Systems',
      packages=['umapi'],
      install_requires=[
            'requests',
            'cryptography==1.2.1',
            'PyJWT',
            'mock',
            'nose>=1.0'
      ],
      zip_safe=False)

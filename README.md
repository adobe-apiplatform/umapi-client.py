# cce-umapi
Python User Management API Interface for Creative Cloud Enterprise

# Installation

1. Clone this repository or download the latest stable release.
2. From the command line, change to the `cce-umapi` directory.
3. To install, run the command `python setup.py install`.  [**NOTE**: You may need admin/root privileges (using `sudo`) to install new packages in your environment.  It is recommended that you use `virtualenv` to make a virtual python environment.  See the [virtualenvwrapper documentation](http://virtualenvwrapper.readthedocs.io/en/latest/index.html) for more information]
4. If you encounter errors that repor missing library files, you may need to install the packages `python-dev`, `libssl-dev` and `libffi-dev` (these are the Debian package names - your environment may vary).
5. (**optional**) To run tests, use the command `python setup.py nosetests`.

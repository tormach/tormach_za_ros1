#!/usr/bin/env python

from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['hal_402_device_mgr', 'hal_402_device_mgr.params'],
    package_dir={'': 'src'},
)

setup(**d)

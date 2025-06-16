#!/usr/bin/env python

import os
import re
from catkin_pkg.python_setup import generate_distutils_setup
from distutils.core import setup


def find_packages(path):
    return [
        re.sub("^[^A-z0-9_]+", "", root[len(path) + 1 :].replace("/", "."))
        for root, dirs, files in os.walk(path)
        if "__init__.py" in files and not root.endswith("/testing")
    ]


# Common package setup
d = dict(
    packages=find_packages("src"),
    package_dir={"": "src"},
)

d = generate_distutils_setup(**d)

setup(**d)

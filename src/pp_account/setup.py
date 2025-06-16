#!/usr/bin/env python

import os
from catkin_pkg.python_setup import generate_distutils_setup
from distutils.core import setup


def find_data():
    topdir = 'src/pp_account'
    res = set()
    for root, dirs, files in os.walk(topdir):
        subdir = root[len(topdir) + 1 :]
        for f in files:
            for ext in '.xml':
                if f.endswith(ext):
                    res.add(f'{subdir}/*{ext}')
    return {'pp_account': list(res)}


# Common package setup
d = dict(
    packages=[
        'pp_account',
        'pp_account.storage',
        'pp_account.storage.secret_service',
        'pp_account.storage.plaintext_file',
        'pp_account.hub',
    ],
    package_dir={'': 'src'},
    package_data=find_data(),
)

d = generate_distutils_setup(**d)

setup(**d)

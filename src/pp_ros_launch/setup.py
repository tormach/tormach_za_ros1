#!/usr/bin/env python

import os

# Common package setup
d = dict(
    packages=[
        'pp_ros_launch',
        'pp_ros_launch.launcher',
        'pp_ros_launch.image',
        'pp_ros_launch.system',
    ],
    package_dir={'': 'src'},
)

if os.environ.get('ENV_COOKIE', 'bare-metal') == 'bare-metal':
    # Setup for plain setuptools on bare metal
    from setuptools import setup

    d = dict(
        name='pp_ros_launch',
        description='PathPilot ROS launcher',
        entry_points={
            'console_scripts': [
                'run_pp_ros=pp_ros_launch.launcher:run',
                'pp_launcher_listener=pp_ros_launch.launcher.rpcinterface:run_listener',
            ]
        },
        install_requires=['requests', 'docker', 'pyyaml', 'semver'],
        include_package_data=True,
        setup_requires=["pytest-runner"],
        tests_require=['pytest', 'mock', 'pytest-cov'],
        zip_safe=True,
        **d
    )
else:
    # Setup for ROS package
    from distutils.core import setup
    from catkin_pkg.python_setup import generate_distutils_setup

    d = generate_distutils_setup(**d)

setup(**d)

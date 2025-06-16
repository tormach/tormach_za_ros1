# PEP561 stubs for the robot_command package

This package holds stubs for the `robot_command` package forming the base of the Tormach Robot Programming Language
(TRPL).

## Installation

To install the stubs, simply mark them as source directory in your IDE (e.g.
[PyCharm](https://www.jetbrains.com/help/pycharm/stubs.html)) or install the Python package.

```bash
python3 setup.py install
```

If you also want to have type completion for the dependency packages, you can install the dependency packages as
follows:

```bash
pip3 install PyKDL pint
```

On Ubuntu you can also install the ROS packages: http://wiki.ros.org/noetic/Installation/Ubuntu

```bash
sudo apt-get install ros-noetic-rospy ros-noetic-geometry-msgs ros-noetic-trajectory-msgs
```

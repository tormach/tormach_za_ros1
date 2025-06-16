#!/bin/bash -xe
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
ROS_BASE_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/ros_base

apt-get update
apt-get install -y wget

###########################
# Set up ROS
###########################
mkdir -p ${WS_DIR}

echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" |
    tee /etc/apt/sources.list.d/ros-latest.list
wget https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc -O - | apt-key add -

apt-get update

apt-get install -y \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    python3-wstool \
    ros-noetic-catkin \
    python3-catkin-tools \
    python3-osrf-pycommon # Forgotten pkg dependency of python3-catkin-tools

apt-get install -y \
    python3-scipy \
    python3-sklearn \
    python3-matplotlib \
    python3-numpy \
    python3-scipy \
    python3-tk

# Debian `ros-catkin-lint` package is broken; install via pip
# https://bugs.launchpad.net/ubuntu/+source/ros-catkin-lint/+bug/1892529
pip3 install \
    catkin-lint

# Install rosdep file with Machinekit keys & update local database
rm -f /etc/ros/rosdep/sources.list.d/20-default.list
rosdep init
echo "yaml file:///etc/ros/rosdep/pp-rosdep.yaml" |
    tee /etc/ros/rosdep/sources.list.d/10-local.list
cp ${ROS_BASE_SCRIPTS_DIR}/pp-rosdep.yaml /etc/ros/rosdep/pp-rosdep.yaml
rosdep update --rosdistro=$ROS_DISTRO

###########################
# Install ROS from packages
###########################
# http://wiki.ros.org/Installation/Ubuntu

# Set up ROS APT repos
cat >/etc/apt/sources.list.d/ros-latest.list <<EOF
deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main
deb-src http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main
EOF

apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' \
    --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654

apt-get update

# Install base ROS distro
apt-get install ros-${ROS_DISTRO}-ros-base

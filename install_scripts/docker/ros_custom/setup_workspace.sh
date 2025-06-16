#!/bin/bash -e
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x

###########################
# Init ROS workspace and download sources
###########################

mkdir -p ${WS_DIR}/src /opt/ros/${ROS_DISTRO}
cd ${WS_DIR}

# Set up new ROS workspace, extending /opt/ros/${ROS_DISTRO}
catkin config --init --install-space /opt/ros/${ROS_DISTRO} --install \
    --merge-install --merge-devel --cmake-args -DCMAKE_BUILD_TYPE=Release

# Download ROS package sources to workspace using generated rosinstall
if test -f ${ROS_DISTRO}.rosinstall; then
    wstool init src ${ROS_DISTRO}.rosinstall
fi

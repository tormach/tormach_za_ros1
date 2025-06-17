#!/bin/bash -e
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x
ROS_CUSTOM_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/ros_custom

apt-get update

###########################
# Build and install custom external packages
###########################

cd ${ROS_CUSTOM_SCRIPTS_DIR}

# Compute and install ROS workspace package dependencies
${ROS_CUSTOM_SCRIPTS_DIR}/run_rosdep.sh

###########################
# YDLIDAR SDK
###########################

# Clone the YDLidar-SDK repository
# FIXME Build broken after upstream changes
# https://github.com/YDLIDAR/YDLidar-SDK/issues/58
# https://github.com/YDLIDAR/YDLidar-SDK/pull/59
# git clone https://github.com/YDLIDAR/YDLidar-SDK.git
git clone https://github.com/hannesduske/YDLidar-SDK.git
cd YDLidar-SDK

# Create build directory
mkdir -p build
cd build

# Run cmake with installation prefix set to /usr/local
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# Compile
make

# Install the library
make install # ...where we can use it now...
DESTDIR=/root/ros_catkin_ws/ros-export \
    make install # ...and where it can be copied to final image

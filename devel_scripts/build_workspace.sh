#!/bin/bash -e
#######################################
# Initialize and build ROS workspace
#######################################

# Set up environment
WANT_ENV=docker-run
source "$(dirname $0)/../install_scripts/env.sh"
cd "${REPO_DIR}"

# Update rosdep cache, once only
if test ! -d ~/.ros/rosdep/sources.cache; then
    rosdep update
fi

# Configure this workspace as an extension of the main one & load environment
catkin config --extend /opt/ros/${ROS_DISTRO} \
    --cmake-args -DCMAKE_BUILD_TYPE=Release

# Build the workspace
catkin build

USER_PROGRAM_PATH=~/nc_files/robot_programs
mkdir -p ${USER_PROGRAM_PATH}
cp -rf src/robot_command/examples/programs/* ${USER_PROGRAM_PATH}

#!/bin/bash -e
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x
ROS_CUSTOM_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/ros_custom
ROS_BASE_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/ros_base

###########################
# Build and install custom external packages
###########################

cd ${ROS_CUSTOM_SCRIPTS_DIR}

# Build and install ROS workspace
${ROS_CUSTOM_SCRIPTS_DIR}/run_catkin_build.sh with_destdir

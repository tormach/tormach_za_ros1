#!/bin/bash -e
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x
ROS_CUSTOM_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/ros_custom

apt-get update

###########################
# Fix ssh git checkouts
###########################

# Only in CI; if a human runs this for some reason, don't clobber the
# user's ssh config
if test ! -d ~/.ssh; then
    mkdir -p ~/.ssh
    cat >~/.ssh/config <<-EOF
	HOST *
	    StrictHostKeyChecking no
	EOF
fi

###########################
# Write .rosinstall
###########################

# Install `update_rosinstall.py` dependencies
apt-get install -y \
    python3-rosinstall-generator

# Generate .rosinstall file
${ROS_CUSTOM_SCRIPTS_DIR}/update_rosinstall.py

# Move file into ROS workspace directory where `setup_workspace.sh`
# script can find it
mkdir -p ${WS_DIR}
mv ${ROS_DISTRO}.rosinstall ${WS_DIR}
cat ${WS_DIR}/${ROS_DISTRO}.rosinstall

###########################
# Set up ROS workspace
###########################

# Set up and configure ROS workspace, and download external source
# distributions
${ROS_CUSTOM_SCRIPTS_DIR}/setup_workspace.sh

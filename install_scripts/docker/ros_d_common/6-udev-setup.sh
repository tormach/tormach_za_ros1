#!/bin/bash -xe
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh

###########################
# Set up UDEV
###########################

cd ros_d_common

# Remove all the rules from the standard udev installation
rm /usr/lib/udev/rules.d/*

# Copy the ruleset file to the image
cp -a 99-tormach.rules /usr/lib/udev/rules.d

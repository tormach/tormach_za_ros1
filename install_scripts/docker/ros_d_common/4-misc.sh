#!/bin/bash -xe
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh

apt-get update
cd ros_d_common

###########################
# Additional software
###########################

# Add Python sh for devel_scripts
apt-get install -y \
    python3-sh

###########################
# Misc. cleanups
###########################

# Fix avahi-daemon in Docker
#   https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=856311#15
sed -i -e '/^rlimit-nproc/ s/^/#/' /etc/avahi/avahi-daemon.conf

# On Debian, LD_LIBRARY_PATH isn't allowed in setuid programs
echo /opt/ros/${ROS_DISTRO}/lib |
    tee /etc/ld.so.conf.d/ros-${ROS_DISTRO}.conf
ldconfig

# Ensure `ethercat` group exists
# (`etherlabmaster` package that creates it isn't installed)
addgroup --system ethercat

# Ensure `robotusers` group exists
# (used for 'sudo' privileges in DIST and DEVEL images both)
addgroup --system robotusers

# Install deps for Qt6
apt-get install -y \
    libxcb-cursor0

# Install Logrotate
apt-get install -y \
    cron \
    anacron \
    logrotate
mkdir -p /etc/pathpilot/
cp logrotate_ros.conf /etc/pathpilot/logrotate_ros.conf

# Install rsyslog
apt-get install -y \
    rsyslog

## Install Firefox web browser
apt-get install -y \
    firefox \
    libpci3

# Install `ip` utility
apt-get install -y \
    iproute2

# Install and configure sudo, allow passwordless execution as the Root
# for 'apt', 'apt-get' and 'pip'
# DEVEL version of image will overwrite this file with wider permission rule
apt-get install -y \
    sudo
echo "%robotusers	ALL=(root:root) NOPASSWD: /usr/bin/apt*,/usr/bin/pip*" >/etc/sudoers.d/passwordless

# Install Experimental TRPL Tending features
pip install git+ssh://git@bitbucket.org/tormachinc/rpl_tending.git@main

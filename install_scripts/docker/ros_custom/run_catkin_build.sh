#!/bin/bash -e
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x

###########################
# Build ROS workspace
###########################

cd ${WS_DIR}

if test "$1" = with_destdir; then
    # Build packages a second time into DESTDIR for transfer to other stages
    # (First build into install space is needed for inter-package dependencies)
    WITH_DESTDIR=true
    shift
fi

# Build packages into install space
run_with_ccache catkin build --status-rate 0.1 -- "${@}"
if ${WITH_DESTDIR:-false}; then
    source /opt/ros/${ROS_DISTRO}/setup.bash
    DESTDIR=/root/ros_catkin_ws/ros-export \
        run_with_ccache catkin build --status-rate 0.1 -- "${@}"
fi

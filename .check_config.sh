#!/bin/bash

ROS_RELEASE=kinetic # ROS release version

#=======================================================================
# verify that PC configuration matches requirements for training class
#=======================================================================

function print_result() {
    if [ $? -eq 0 ]; then # check command result
        echo -e "\e[00;32m[OK]\e[00m"
    else
        echo -e "\e[00;31m[FAIL]\e[00m"
    fi
}

function check_deb() {
    printf "  - %-30s" "$1:"
    print_result $(dpkg-query -s $1 &>/dev/null)
}

function check_debs() {
    echo "Checking debian packages... "
    check_deb meld
    check_deb ros-$ROS_RELEASE-desktop-full
    check_deb ros-$ROS_RELEASE-moveit
    check_deb ros-$ROS_RELEASE-industrial-core
    check_deb python-catkin-tools
    # This one doesn't seem to actually exist
    # check_deb qt57creator-plugin-ros
    check_deb ros-$ROS_RELEASE-openni-launch
    check_deb ros-$ROS_RELEASE-openni-camera
    check_deb ros-$ROS_RELEASE-openni2-launch
    check_deb ros-$ROS_RELEASE-openni2-launch
    check_deb build-essential
    check_deb libfontconfig1
    check_deb mesa-common-dev
    check_deb libglu1-mesa-dev
    check_deb pcl-tools
}

function check_bashrc() {
    echo "Checking .bashrc... "
    printf "  - %-30s" "\$ROS_ROOT:"
    if [ -z ${ROS_ROOT+x} ]; then
        print_result $(false)
    else
        print_result $([ $ROS_ROOT == "/opt/ros/$ROS_RELEASE/share/ros" ])
    fi
}

#---------------------------------------
# run the actual tests
#---------------------------------------

check_debs
check_bashrc

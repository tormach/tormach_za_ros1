#!/bin/bash -e
#
# Run `rosdep install` to install all apt and pip dependencies for ROS
# packages in /opt/ros/${ROS_DISTRO} and optionally ./src

WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x
BASE_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/base

ROSDEP_SKIP_KEYS=(
    # moveit distro packages not in noetic yet
    # - top-level
    moveit_commander
    moveit_core
    moveit_kinematics
    moveit_setup_assistant
    # - moveit_planners
    moveit_planners_ompl
    # - moveit_ros
    moveit_ros_benchmarks
    moveit_ros_move_group
    moveit_ros_planning_interface
    moveit_ros_visualization
    moveit_servo
    # - moveit_plugins
    moveit_fake_controller_manager

    # Other packages not in noetic yet
    moveit_msgs

    # pilz industrial motion deps
    orocos_kdl
    prbt_pg70_support
    prbt_moveit_config
    prbt_support
)

for DIR in ${WS_DIR}/src /opt/ros/${ROS_DISTRO}; do
    if test -d $DIR; then
        ROSDEP_ARGS+=" --from-paths $DIR"
    fi
done
ROSDEP_ARGS+=" ${ROSDEP_SKIP_KEYS[*]/#/--skip-keys=}"

cd ${WS_DIR}
if test -f /opt/ros/${ROS_DISTRO}/setup.bash; then
    # rosdep needs this to pick up package deps already installed
    # - don't exit at OpenRAVE env hook
    # https://github.com/jsk-ros-pkg/openrave_planning/blob/master/openrave/env-hooks/99.openrave.sh.in
    set +e
    source /opt/ros/${ROS_DISTRO}/setup.bash
    set -e
fi

# Create script to install ROS package dependencies
DEPS=${BASE_SCRIPTS_DIR}/install_local_package_deps.sh
# - Generate bash script
rosdep install --simulate --ignore-src ${ROSDEP_ARGS} |
    sort | grep -v '^#' >${DEPS}
cat ${DEPS}

# Run script
if test "$1" != no_install; then
    apt-get update
    bash -xe ${DEPS}
fi

#!/bin/bash -e
#
# Run `rosdep install` to install all apt and pip dependencies for ROS
# packages in /opt/ros/${ROS_DISTRO} and optionally ./src

WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
set -x
BASE_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/base

ROSDEP_SKIP_KEYS=(
    # - these metapackages don't actually install anything and raise errors:
    #    ERROR: the following packages/stacks could not have their
    #    rosdep keys resolved to system dependencies:
    #    za6_moveit_config: No definition of
    #       [rqt_robot_plugins] for OS [debian]
    rqt_robot_plugins
    rqt_common_plugins
    # OpenRAVE is built by hand
    openrave
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

# Install ROS package dependencies
DEPS=${BASE_SCRIPTS_DIR}/install_local_package_deps.sh
# - Generate bash script
rosdep install --simulate --ignore-src ${ROSDEP_ARGS} >${DEPS}

# - HACK:  Install py2-compatible pymachinetalk
sed -i ${DEPS} -e 's/pymachinetalk/pymachinetalk==0.12.2/'

# - Run script
apt-get update
bash -xe ${DEPS}

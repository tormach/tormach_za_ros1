#!/bin/bash -e
#
# Run unit tests in Docker

# List of packages to ignore
SKIP_PKGS=(
    # Auto-generated package
    za6_moveit_config
)

usage() {
    if test -z "$*"; then
        RC=0
    else
        echo "Error:  $*" >&2
        RC=1
    fi
    cat >&2 <<EOF
Usage:  $0 [args...]
    -C:  Run with CI settings (like -gUFxcbdlt)
    -g:  Clean and reset git tree WARNING:  DESTROYS UNCOMMITTED CHANGES
    -U:  Update pre-commit formatters
    -f:  Run formatters
    -c:  Configure workspace
    -b:  Build workspace (devel image only)
    -d:  Update rosdep
    -l:  Run catkin lint
    -t:  Run catkin tests
    -D:  Build rosdep docs
    -y:  'Yes' mode: don't prompt
    -h:  Show this help message
EOF
    exit $RC
}
if test -z "${ENV_CI}" -a -z "$*"; then
    usage
fi

if test $IMAGE_TYPE = dist; then
    SETUP_SCRIPT=/opt/ros/${ROS_DISTRO}/setup.bash
    DEVEL_IMAGE=false
else
    SETUP_SCRIPT=devel/setup.bash
    DEVEL_IMAGE=true
fi

set_all() {
    # Do the full shebang (except docs)
    SHOW_DEBUGGING=true
    CLEAN_GIT=true
    UPDATE_PRE_COMMIT=$DEVEL_IMAGE # no dev tools in dist image
    RUN_FORMATTERS=$DEVEL_IMAGE
    CONFIGURE_WORKSPACE=true
    BUILD_WORKSPACE=true
    UPDATE_ROSDEP=true
    RUN_LINT=true
    RUN_TESTS=true
    BUILD_DOCS=true
}

while getopts :CgUfcbdltDyh ARG; do
    case $ARG in
    C) set_all ;;
    g) CLEAN_GIT=true ;;
    U) UPDATE_PRE_COMMIT=true ;;
    f) RUN_FORMATTERS=true ;;
    c) CONFIGURE_WORKSPACE=true ;;
    b) BUILD_WORKSPACE=true ;;
    d) UPDATE_ROSDEP=true ;;
    l) RUN_LINT=true ;;
    t) RUN_TESTS=true ;;
    D) BUILD_DOCS=true ;;
    y) YES_MODE=true ;;
    h) usage ;;
    *) usage "Unknown option '-$ARG'" ;;
    esac
done
shift $(($OPTIND - 1))

if test -n "${ENV_CI}"; then
    # Do the full shebang in CI mode, no questions asked
    echo "Running in CI mode"
    set_all
    YES_MODE=true
fi

if ${SHOW_DEBUGGING:-false}; then
    # Show installed software versions in CI for debugging
    echo "Installed Debian packages:"
    dpkg-query -W
    echo
    echo "Installed pip3 packages:"
    pip3 list --format=columns
fi

# Show what we're doing
set -x

if ${CLEAN_GIT:-false}; then
    # Clean up ignored files; uncommitted files aren't touched to make
    # this safer in a dev environment
    sudo git clean -Xdf
fi

if ${UPDATE_PRE_COMMIT:-false}; then
    pre-commit autoupdate \
        --repo https://github.com/pre-commit/pre-commit-hooks
fi

if ${RUN_FORMATTERS:-false}; then
    # Run formatters
    pre-commit run --all-files || FAIL=1
    if test -n "${FAIL}"; then
        test -z "${ENV_CI}" || (git diff | head -500) # Show diff in CI
        exit 1
    fi
fi

if ${CONFIGURE_WORKSPACE:-false}; then
    # Configure the workspace
    if $DEVEL_IMAGE; then
        catkin config --extend /opt/ros/${ROS_DISTRO}
    else
        catkin config --init --install-space /opt/ros/${ROS_DISTRO} \
            --merge-devel --install
    fi
fi

if ${BUILD_WORKSPACE:-false}; then
    # Build the workspace
    catkin build --status-rate 0.1 --cmake-args -Werror=dev
fi

if ${UPDATE_ROSDEP:-false}; then
    # Update rosdep sources; this can avoid "unknown dependencies will
    # be ignored" message in CI during `catkin lint`
    rosdep update
fi

if ${RUN_LINT:-false}; then
    # Run catkin lint
    source $SETUP_SCRIPT
    catkin lint -W 2 --strict ${SKIP_PKGS[*]/#/--skip-pkg=} ${IGNORE_DIAGNOSTIC[*]/#/--ignore=} --explain src/
fi

if ${RUN_TESTS:-false}; then
    # Build and run the tests
    source $SETUP_SCRIPT
    catkin run_tests -p 1 --status-rate 0.1 --cmake-args -Werror=dev
    catkin_test_results
fi

if ${BUILD_DOCS:-false}; then
    # Build rosdoc_lite docs
    source $SETUP_SCRIPT
    had_error=false
    for PKG in $(catkin list -u); do
        PKG_PATH=$(rospack find $PKG)
        if test -f ${PKG_PATH}/rosdoc.yaml; then
            { err=$(rosdoc_lite $PKG_PATH 2>&1 >&3 3>&-); } 3>&1
            echo >&2 "${err}"
            if echo ${err} | grep "ERROR"; then
                had_error=true
            fi
        fi
    done
    if ${had_error}; then
        echo >&2 "Error during doc build"
        exit 1
    fi
fi

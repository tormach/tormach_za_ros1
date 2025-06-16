#!/bin/bash -e
# Run tests in the Docker image
#
# This script should be able to run in CI or in a dev environment.
#
# Set up two build steps in CI calling this script, one with `ci.sh
# devel`, one with `ci.sh dist`
IMAGE_TYPE=$1
test "$IMAGE_TYPE" = devel && DEVEL_IMAGE=true || DEVEL_IMAGE=false

if test "$IMAGE_TYPE" != dist -a "$IMAGE_TYPE" != devel; then
    echo "Usage:  $0 [ dist | devel ]" 1>&2
    exit 1
fi

echo "*****************************"
echo "Running tests for $IMAGE_TYPE"
echo "*****************************"
set -x

# Set up
CONTAINER=ros-${IMAGE_TYPE}-test
if test -n "$TEAMCITY_VERSION" -o -n "$GITHUB_ACTIONS"; then
    # Running on TeamCity agent or in GitHub Actions
    export ENV_CI=1
    IN_CI=true
    if test -n "$TEAMCITY_VERSION"; then
        CI_USER=buildagent
        ORIG_UID_GID=1000:1000
    else # GitHub Actions
        CI_USER=$(id -un)
        ORIG_UID_GID=$(stat -c %u:%g ~)
    fi
    # Clean up after old run
    docker ps
    docker kill $CONTAINER >&/dev/null || true
    # Debugging
    env
    sleep 1 # Let stderr & stdout catch up in CI
else
    # Running outside CI (developer's box, maybe)
    IN_CI=false
    CI_USER=$(id -un)
    ORIG_UID_GID=$(stat -c %u:%g ~)
fi

if $DEVEL_IMAGE; then
    # Run tests as regular user
    DOCKER_EXEC_ARGS=(-tu $CI_USER)
else # dist image
    # Run dist image
    DOCKER_DEV_ARGS+=" -d"
    # Run tests as root in dist img (installs to /opt/ros)
    DOCKER_EXEC_ARGS=(-tu root -e HOME=/root)
fi

EXIT_HANDLER_SIGNALS="1 2 3 9 15 EXIT"
cleanup_and_exit() {
    # Remove signal handler, clean up, and exit
    trap - ${EXIT_HANDLER_SIGNALS} EXIT

    test -z "$2" || echo "$2" 1>&2

    # Clean up:
    # - Be sure detached container gets cleaned up
    docker logs $CONTAINER || true
    sleep 1 # Let stderr & stdout catch up in CI
    docker ps
    docker kill $CONTAINER >&/dev/null || true
    # - Clean up build artifacts to avoid dirtying `dist` img build
    #   cache in CI (this runs in `devel` img)
    install_scripts/docker-dev.sh -n ros-test-cleanup \
        sudo git clean -xdf
    # ...and exit
    exit $1
}
trap "cleanup_and_exit 1" $EXIT_HANDLER_SIGNALS

# Start container in background
install_scripts/docker-dev.sh -n ${CONTAINER} -k ${DOCKER_DEV_ARGS}

# Wait for container to become ready
while ! docker exec -tu $CI_USER $CONTAINER id >&/dev/null; do
    sleep 1
    test $((i += 1)) -lt 40 || # Wait up to 40 seconds
        cleanup_and_exit 5 "Timeout waiting for container"
done

# Avoid this error
# fatal: detected dubious ownership in repository at
#     '/opt/buildagent/work/ba1ace9db7d41c40'
test $TEST_USER != root ||
    docker exec "${DOCKER_EXEC_ARGS[@]}" $CONTAINER \
        git config --global --add safe.directory $PWD

# Start X server as root in container
docker exec -d $CONTAINER \
    Xorg -noreset +extension GLX +extension RANDR +extension RENDER \
    -logfile /var/log/xorg.log -config /etc/pathpilot/xorg.conf :1
DOCKER_EXEC_ARGS+=(-e DISPLAY=:1)

# Exec tests
RUN_TESTS_ARGS=${RUN_TESTS_ARGS:--C}
docker exec "${DOCKER_EXEC_ARGS[@]}" $CONTAINER \
    install_scripts/run_tests.sh $RUN_TESTS_ARGS

# Exit, cleaning up container
cleanup_and_exit $?

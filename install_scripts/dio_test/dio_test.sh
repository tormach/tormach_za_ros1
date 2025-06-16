#!/bin/bash -xe

IMAGE=$(docker images --filter label=ROBOT_MODEL=za -q | head -1)
if test -z "${IMAGE}"; then
    echo "No images found" >&2
    exit 1
fi

DIR=$(readlink -f $(dirname $0))

exec docker run --rm -it \
    --privileged \
    -e UID=$(id -u) -e GID=$(id -g) -e USER \
    -e HOME \
    -v $HOME:$HOME \
    -v /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket \
    -v /dev/EtherCAT0:/dev/EtherCAT0 \
    -v $DIR:$DIR \
    -w $DIR \
    ${IMAGE} \
    bash -c 'realtime start; exec python dio_test_setup.py'

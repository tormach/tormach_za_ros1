from .subsystem import (
    SubSystem,
    SubSystemDockerEnvCheck,
    SubSystemDockerVolumeCheck,
)


class DbusSessionBusAddress(SubSystemDockerEnvCheck):
    """Get the DBus session bus address from the environment.

    Checks the ``DBUS_SESSION_BUS_ADDRESS`` environment variable
    value, e.g. ``unix:abstract=/tmp/dbus-cMaBPC7Qh2``, and adds it to
    docker container run args.
    """

    name = 'dbus_session_bus_address'
    env_vars = ["DBUS_SESSION_BUS_ADDRESS"]


class SystemBusSocketPath(SubSystemDockerVolumeCheck):
    """Bind-mount the DBus system bus socket into the container."""

    name = 'system_bus_socket_path'
    path = "/var/run/dbus/system_bus_socket"


class Dbus(SubSystem):
    """Pass DBus access in to Docker container."""

    name = "dbus"

    check_classes = [DbusSessionBusAddress, SystemBusSocketPath]

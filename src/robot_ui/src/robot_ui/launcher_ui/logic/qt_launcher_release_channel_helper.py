"""Handler functions for processing the instances of pathpilot_versions
module objects in the PathPilot Robot Launcher code

This should limit the exposure of the VersionChannel type
"""

from pp_ros_launch.image.pathpilot_versions import (
    VersionChannel,
    VersionChannelSet,
)
from PySide6.QtCore import QObject

from typing import Union

known_channels = {
    'ros_public': 'ROS Public',
    'robot_alpha': 'Robot Alpha',
    'robot_beta': 'Robot Beta',
    'robot_testing': 'Robot Testing',
}


def get_label(
    channel_name: Union[str, VersionChannel, VersionChannelSet],
    qobject: QObject,
) -> str:
    """Mapping function between PathPilot Robot raw name
    as know and used by the OCI registry and Docker daemon
    and the user facing name (typically capitalization)

    Args:
        channel_name (Union[str,
                            VersionChannel,
                            VersionChannelSet]): PathPilot Robot release channel
                                                 name or the channel object
        qobject (QObject): Qt calling object

    Returns:
        str: User facing pretty name
    """
    if isinstance(channel_name, VersionChannel) or isinstance(
        channel_name, VersionChannelSet
    ):
        channel_name = get_raw_name(channel_name, qobject)
    if not isinstance(channel_name, str) or channel_name == '':
        return qobject.tr('Unknown release channel')
    label = qobject.tr(known_channels.get(channel_name, None))
    if not label:
        label = qobject.tr(channel_name.replace('_', ' ').title())
    return label


def get_raw_name(
    channel: Union[VersionChannel, VersionChannelSet], qobject: QObject
) -> str:
    """Getter for the raw PathPilot Robot release channel name
    as used by the OCI registry or by Docker daemon

    Args:
        channel (Union[VersionChannel, VersionChannelSet]): PathPilot Robot release channel
        qobject (QObject): Qt calling object

    Raises:
        RuntimeError: Invalid PathPilot Robot release channel object

    Returns:
        str: PathPilot Robot release channel raw name
    """
    if getattr(channel, 'name', None) is None:
        raise RuntimeError('Unknown release channel')

    return channel.name

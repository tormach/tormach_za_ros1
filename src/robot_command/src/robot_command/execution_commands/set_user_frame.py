from typing import Union, Optional

from .frame_commands import SetFrameCommand
from ..interfaces import (
    UserFrameInterfaceSingleton,
)
from ..rpl import Pose


class SetUserFrame(SetFrameCommand):
    name = 'set_user_frame'
    NO_FRAME_NAME = 'world'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(
        self,
        name: str,
        pose: Optional[Union[Pose, str]] = None,
        position: Optional[Union[Pose, str]] = None,
        orientation: Optional[Union[Pose, str]] = None,
    ):
        """
        Sets a user frame using a pose, position or orientation or clears an frame.

        The position and orientation arguments can be combined to overwrite the
        pose’s position or orientation.

        :param name: Name of the user frame
        :param pose: Pose to use for the user frame
        :param position: Use the position of this pose to override the position of the pose.
        :param orientation: Use the orientation of this pose to override the orientation of the pose.

        **Examples**

        .. code-block:: python

            set_user_frame("table", p[0, 100, 0, 0, 0, 0])
            set_user_frame("frame_1", waypoint_2, orientation=Pose(a=90))
            set_user_frame("frame_1") # clears frame_1
        """
        super().__init__(name, pose, position, orientation)

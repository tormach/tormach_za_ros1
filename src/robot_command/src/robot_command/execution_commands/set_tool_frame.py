from typing import Union

from .frame_commands import SetFrameCommand
from ..interfaces import (
    ToolFrameInterfaceSingleton,
)
from ..rpl import Pose


class SetToolFrame(SetFrameCommand):
    name = 'set_tool_frame'
    NO_FRAME_NAME = 'none'
    FRAME_INTERFACE = ToolFrameInterfaceSingleton

    def __init__(
        self,
        name: str,
        pose: Union[Pose, str] = None,
        position: Union[Pose, str] = None,
        orientation: Union[Pose, str] = None,
    ):
        """
        Sets a tool frame using a pose, position or orientation or clears an frame.

        The position and orientation arguments can be combined to overwrite the
        pose’s position or orientation.

        :param name: Name of the tool frame
        :param pose: Pose to use for the tool frame
        :param position: Use the position of this pose to override the position of the pose.
        :param orientation: Use the orientation of this pose to override the orientation of the pose.

        **Examples**

        .. code-block:: python

            set_tool_frame("some_tool", p[0, 0, 100, 0, 0, 0])
            set_tool_frame("other_tool", waypoint_2, position=Pose(z=0.1))
            set_tool_frame("other_tool") # clears frame other_tool
        """
        super().__init__(name, pose, position, orientation)

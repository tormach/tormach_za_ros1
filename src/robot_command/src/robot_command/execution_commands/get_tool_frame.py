from .frame_commands import GetFrameCommand
from ..interfaces import (
    ToolFrameInterfaceSingleton,
)


class GetToolFrame(GetFrameCommand):
    name = 'get_tool_frame'
    FRAME_INTERFACE = ToolFrameInterfaceSingleton

    def __init__(self, name: str):
        """
        Returns the pose of a tool frame.

        :param name: Name of the tool frame.
        :return: Pose of the user frame or None if it does not exist.
        :raises TypeError: if no tool frame with the name is found

        **Examples**

        .. code-block:: python

            pose = get_tool_frame("tool1")
        """
        super().__init__(name)

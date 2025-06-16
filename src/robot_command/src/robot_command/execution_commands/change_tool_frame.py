from typing import Union

from .frame_commands import ChangeFrameCommand
from ..interfaces import ToolFrameInterfaceSingleton


class ChangeToolFrame(ChangeFrameCommand):
    name = 'change_tool_frame'
    FRAME_INTERFACE = ToolFrameInterfaceSingleton

    def __init__(self, name: Union[str, None]):
        """
        Change the currently active tool frame. If an empty string or ``None`` is
        used as the name parameter, the empty tool frame *none* becomes active.

        :param name: The name of the tool frame to activate or `None` to disable tool frames.

        **Examples**

        .. code-block:: python

            change_tool_frame("table")
            change_tool_frame(None) # disable any active frames
        """
        super().__init__(name)

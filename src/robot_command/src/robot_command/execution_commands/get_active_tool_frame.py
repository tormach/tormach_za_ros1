from .frame_commands import GetActiveToolFrameCommand
from ..interfaces import (
    ToolFrameInterfaceSingleton,
)


class GetActiveToolFrame(GetActiveToolFrameCommand):
    name = 'get_active_tool_frame'
    FRAME_INTERFACE = ToolFrameInterfaceSingleton

    def __init__(self):
        """
        Returns the name of the active tool frame.

        **Examples**

        .. code-block:: python

            active_tool_frame_name = get_active_tool_frame()
        """
        super().__init__()
        self.active_frame_name = self.FRAME_INTERFACE().active_frame

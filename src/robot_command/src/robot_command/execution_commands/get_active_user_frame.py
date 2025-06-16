from .frame_commands import GetActiveUserFrameCommand
from ..interfaces import (
    UserFrameInterfaceSingleton,
)


class GetActiveUserFrame(GetActiveUserFrameCommand):
    name = 'get_active_user_frame'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(self):
        """
        Returns the name of the active user frame.

        **Examples**

        .. code-block:: python

            active_user_frame_name = get_active_user_frame()
        """
        super().__init__()
        self.active_frame_name = self.FRAME_INTERFACE().active_frame

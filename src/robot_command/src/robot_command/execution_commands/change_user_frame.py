from typing import Union

from .frame_commands import ChangeFrameCommand
from ..interfaces import UserFrameInterfaceSingleton


class ChangeUserFrame(ChangeFrameCommand):
    name = 'change_user_frame'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(self, name: Union[str, None]):
        """
        Change the currently active user frame. If an empty string or ``None`` is
        used as the name parameter, the empty user frame *world* becomes active.

        :param name: The name of the tool frame to activate or `None` to disable user frames.

        **Examples**

        .. code-block:: python

            change_user_frame("table")
            change_user_frame(None) # disable any active frames
        """
        super().__init__(name)

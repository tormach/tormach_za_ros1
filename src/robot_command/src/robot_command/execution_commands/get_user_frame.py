from .frame_commands import GetFrameCommand
from ..interfaces import (
    UserFrameInterfaceSingleton,
)


class GetUserFrame(GetFrameCommand):
    name = 'get_user_frame'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(self, name: str):
        """
        Returns the pose of a user frame.

        :param name: Name of the user frame.
        :return: Pose of the user frame.
        :raises TypeError: if no user frame with the name is found

        **Examples**

        .. code-block:: python

            pose = get_user_frame("table")
        """
        super().__init__(name)

from .to_local_pose import ToLocalPose
from ..interfaces import (
    JointsToPoseInterfaceSingleton,
)


class GetPose(ToLocalPose):
    name = 'get_pose'

    def __init__(
        self, apply_user_frame: bool = True, apply_tool_frame: bool = True
    ):
        """
        Returns the current robot pose.

        :param apply_user_frame: Applies the active user frame to the world pose.
        :param apply_tool_frame: Applies the active tool frame to the world pose.
        :return: Current robot pose.

        **Examples**

        .. code-block:: python

            current_pose = get_pose()
        """
        super().__init__(None, apply_user_frame, apply_tool_frame)
        self._joints_to_pose = JointsToPoseInterfaceSingleton()

    def get_pose_to_convert(self):
        return self._joints_to_pose.get_current_pose().pose

    # Note: use parent execute method to convert current pose to local

import rospy
import time

from ..rpl import Command, Pose
from .constants import SLEEP_TIME


class ToLocalPose(Command):
    name = 'to_local_pose'

    def __init__(
        self,
        global_pose,
        apply_work_offset: bool = True,
        apply_tool_offset: bool = True,
    ):
        """
        Converts a global pose to a local pose

        :param global_pose: Global workspace Pose to convert to local coordinates (based on specified arguments)
        :param apply_work_offset: Applies the active work offset
        :param apply_tool_offset: Applies the active tool offset
        :return: converted local pose

        **Examples**

        .. code-block:: python

            local_pose = to_local_pose(global_pose)
            work_only_pose = to_local_pose(global_pose, apply_tool_offset=False)
        """
        super().__init__()

        self.apply_work_offset = apply_work_offset
        self.apply_tool_offset = apply_tool_offset
        self.global_pose_in = global_pose

    def execute(self) -> Pose:
        rospy.logdebug(f'executing {self.name}')
        time.sleep(SLEEP_TIME)

        return Pose()

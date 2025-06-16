import sys

from moveit_commander import (
    roscpp_initialize,
    MoveGroupCommander,
    roscpp_shutdown,
)


class RandomPoseGenerator:
    def __init__(self, group_name, tool_frame):
        self._group_name = group_name
        self._tool_frame = tool_frame

        roscpp_initialize(sys.argv)
        self._manipulator = MoveGroupCommander(group_name)

    def generate_poses(self, count):
        return [
            self._manipulator.get_random_pose(self._tool_frame)
            for _ in range(count)
        ]

    def shutdown(self):
        self._manipulator.stop()
        roscpp_shutdown()

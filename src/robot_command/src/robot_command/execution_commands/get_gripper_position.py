import rospy

from ..rpl import Command
from ..interfaces import (
    GripperInterfaceSingleton,
)


class GetGripperPosition(Command):
    name = 'get_gripper_position'

    def __init__(self):
        """
        Returns the current gripper position.

        :return: Current gripper position.

        **Examples**

        .. code-block:: python

            gripper_position = get_gripper_position()
        """
        super().__init__()
        self._gripper = GripperInterfaceSingleton()

    def execute(self) -> float:
        rospy.logdebug(f'executing {self.name}')
        return self._gripper.current_position / 100.0

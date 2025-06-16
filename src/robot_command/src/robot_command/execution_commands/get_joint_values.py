import rospy

from ..rpl import Command, Joints
from ..interfaces import (
    ConfigInterfaceSingleton,
    JointsToPoseInterfaceSingleton,
)


class GetJointValues(Command):
    name = 'get_joint_values'

    def __init__(self):
        """
        Returns the current joint values.

        :return: Current joint values.

        **Examples**

        .. code-block:: python

            joint_value = get_joint_values()
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()
        self._joints_to_pose = JointsToPoseInterfaceSingleton()

    def execute(self) -> Joints:
        rospy.logdebug(f'executing {self.name}')

        joints = Joints.from_list(
            self._joints_to_pose.get_current_joint_values()
        )
        return joints.from_ros_units(self._config.angular_unit)

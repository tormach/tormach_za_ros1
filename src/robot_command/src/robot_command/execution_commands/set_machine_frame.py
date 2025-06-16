from typing import Union

import rospy

from ..rpl import Command, Pose
from ..interfaces import (
    MachinetalkInterfaceSingleton,
    GlobalWaypointInterfaceSingleton,
    ConfigInterfaceSingleton,
)


class SetMachineFrame(Command):
    name = 'set_machine_frame'

    def __init__(self, pose: Union[Pose, str], instance: str = ''):
        """
        Sets the origin frame for the 3D visualization of the PathPilot remote
        machine model.

        :param pose:  Pose to use for the machine frame.
        :param instance: Optional machine instance name. If not given, default instance is used.

        **Examples**

        .. code-block:: python

            set_machine_frame(p[0,0,0,90,0,0], "instance")
            set_machine_frame(Pose(x=100))  # sets frame for default instance
        """
        super().__init__()
        self._machinetalk = MachinetalkInterfaceSingleton()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()
        self._config = ConfigInterfaceSingleton()

        if isinstance(instance, str):
            self.instance = instance
        else:
            raise TypeError('Optional instance parameter must be a string.')

        if isinstance(pose, str):
            pose = self._global_waypoints.get_global_waypoint(pose)

        if not isinstance(pose, Pose):
            raise TypeError(f'{self.name} requires Pose type as first argument')
        self.pose = pose
        self.instance = instance

    def execute(self) -> None:
        rospy.logdebug(f'executing {self.name}: {self.instance} {self.pose}')
        self._machinetalk.update_pose(
            pose=self.pose.to_ros_units(
                self._config.linear_unit, self._config.angular_unit
            ).to_list(),
            instance=self.instance,
        )

    def __str__(self):
        return f'{self.name}: {self.instance} {self.pose}'

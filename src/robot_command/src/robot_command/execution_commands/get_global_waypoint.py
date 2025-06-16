from typing import Union

import rospy

from ..rpl import Command, Pose, Joints
from ..interfaces import (
    GlobalWaypointInterfaceSingleton,
    ConfigInterfaceSingleton,
)


class GetGlobalWaypoint(Command):
    name = 'get_global_waypoint'

    def __init__(self, name: str):
        """
        Get global waypoint pose or joints value.

        :param name: Name of the global waypoint.
        :return: Pose or Joints of the global waypoint or None if it does not exist.

        **Examples**

        .. code-block:: python

            point = get_global_waypoint("point")
        """

        super().__init__()
        self._config = ConfigInterfaceSingleton()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()

        if not isinstance(name, str):
            raise TypeError(
                "Global waypoint name must be specified as first argument."
            )

        self.waypoint_name = name

    def execute(self) -> Union[Pose, Joints, None]:
        rospy.logdebug(f"executing {self.name}: {self.waypoint_name}")
        try:
            value = self._global_waypoints.get_global_waypoint(
                self.waypoint_name
            )
        except KeyError:
            return None
        else:
            return value.from_ros_units(
                self._config.linear_unit,
                self._config.angular_unit,
            )

    def __str__(self):
        return f"{self.name}: {self.waypoint_name}"

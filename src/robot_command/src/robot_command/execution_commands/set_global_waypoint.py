from typing import Union

import rospy

from ..rpl import Command, Pose, Joints
from ..interfaces import (
    GlobalWaypointInterfaceSingleton,
    ConfigInterfaceSingleton,
)


class SetGlobalWaypoint(Command):
    name = 'set_global_waypoint'

    def __init__(self, name: str, value: Union[Pose, Joints]):
        """
        Set global waypoint pose or joints value.

        :param name: Name of the global waypoint
        :param value: Pose or joints value

        **Examples**

        .. code-block:: python

            set_global_waypoint("point", p[500.0, 0.0, 900.0, 0.0, -90.0, 0.0])
        """
        super().__init__()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()
        self._config = ConfigInterfaceSingleton()
        if not isinstance(name, str):
            raise TypeError(
                "Global waypoint name must be specified as first argument."
            )

        if not isinstance(value, (Pose, Joints)):
            raise TypeError("Second argument must be Pose or Joints type.")

        self.waypoint_name = name
        self.value = value

    def execute(self) -> None:
        rospy.logdebug(
            f"executing {self.name}: {self.waypoint_name} {self.value}"
        )

        self._global_waypoints.set_global_waypoint(
            self.waypoint_name,
            self.value.to_ros_units(
                self._config.linear_unit, self._config.angular_unit
            ),
        )

    def __str__(self):
        return f"{self.name}: {self.waypoint_name} {self.value}"

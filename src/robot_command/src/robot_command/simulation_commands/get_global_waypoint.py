import rospy

from ..rpl import Command, Joints
from ..interfaces import GlobalWaypointInterfaceSingleton


class GetGlobalWaypoint(Command):
    name = 'get_global_waypoint'

    def __init__(self, name):
        super().__init__()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()

        if not isinstance(name, str):
            raise TypeError(
                "Global waypoint name must be specified as first argument."
            )

        self.waypoint_name = name

    def execute(self):
        rospy.logdebug(f"executing get_global_waypoint: {self.waypoint_name}")
        return Joints()

    def __str__(self):
        return f"{self.name}: {self.waypoint_name}"

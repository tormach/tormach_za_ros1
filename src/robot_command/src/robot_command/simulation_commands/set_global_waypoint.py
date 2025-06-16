import rospy

from ..rpl import Command


class SetGlobalWaypoint(Command):
    name = 'set_global_waypoint'

    def __init__(self, name, value):
        super().__init__()
        self.waypoint_name = name
        self.value = value

    def execute(self):
        rospy.logdebug(
            f"executing set_global_waypoint: {self.waypoint_name} {self.value}"
        )

    def __str__(self):
        return f"{self.name}: {self.waypoint_name} {self.value}"

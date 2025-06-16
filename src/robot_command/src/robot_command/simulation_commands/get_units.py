import rospy

from ..rpl import Command


class GetUnits(Command):
    name = 'get_units'

    def __init__(self, with_time: bool = False):
        super().__init__()
        self.with_time = with_time

    def execute(self):
        rospy.logdebug(f'executing {self.name}')

        return "mm", "rad", "s" if self.with_time else "mm", "rad"

import rospy

from ..rpl import Command


class GetGripperPosition(Command):
    name = 'get_gripper_position'

    def __init__(self):
        super().__init__()

    def execute(self):
        rospy.logdebug(f'executing {self.name}')
        return 0.0

    def __str__(self):
        return f'{self.name}'

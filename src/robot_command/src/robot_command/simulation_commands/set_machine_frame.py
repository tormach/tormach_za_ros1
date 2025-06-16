import rospy

from ..rpl import Command


class SetMachineFrame(Command):
    name = 'set_machine_frame'

    def __init__(self, pose, instance=''):
        super().__init__()
        self.pose = pose
        self.instance = instance

    def execute(self):
        rospy.logdebug(
            'executing set_machine_frame: {} {}'.format(
                self.instance, self.pose
            )
        )

    def __str__(self):
        return f'{self.name}: {self.instance} {self.pose}'

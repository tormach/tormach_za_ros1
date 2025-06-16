import rospy

from ..rpl import Command


class ActuateGripper(Command):
    name = 'actuate_gripper'

    def __init__(self, position: float, effort: float = 0.2, wait: bool = True):
        super().__init__()

        self.position = position
        self.effort = effort
        self.wait = wait

    def execute(self):
        rospy.logdebug(
            f'executing {self.name}: {self.position} {self.effort} {self.wait}'
        )

    def _str__(self):
        return f'{self.name}: {self.position} {self.effort} {self.wait}'

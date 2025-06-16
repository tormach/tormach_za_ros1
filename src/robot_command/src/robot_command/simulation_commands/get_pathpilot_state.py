import rospy

from ..rpl import Command


class GetPathPilotState(Command):
    name = 'get_pathpilot_state'

    def __init__(self, instance=''):
        super().__init__()
        self.instance = instance

    def execute(self):
        rospy.logdebug(
            f'executing get_pathpilot_state: instance={self.instance}'
        )
        return 'idle'

    def __str__(self):
        return f'{self.name}: {self.instance}'

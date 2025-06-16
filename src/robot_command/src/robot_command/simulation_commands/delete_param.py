import rospy

from ..rpl import Command


class DeleteParam(Command):
    name = 'delete_param'

    def __init__(self, name):
        super().__init__()

        if not isinstance(name, str):
            raise TypeError(
                'Parameter key must be specified as first argument.'
            )
        self.key = name

    def execute(self):
        rospy.logdebug(f'executing delete_param: {self.key}')

    def __str__(self):
        return f'{self.name}: {self.key}'

import rospy

from ..rpl import Command


class SetParam(Command):
    name = 'set_param'

    def __init__(self, name, value):
        super().__init__()

        if not isinstance(name, str):
            raise TypeError(
                'Parameter key must be specified as first argument.'
            )
        self.key = name
        self.value = value

    def execute(self):
        rospy.logdebug(f'executing set_param: {self.key} {self.value}')

    def __str__(self):
        return f'{self.name}: {self.key} {self.value}'

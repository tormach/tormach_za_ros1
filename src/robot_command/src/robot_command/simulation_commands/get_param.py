import rospy

from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton


class GetParam(Command):
    name = 'get_param'

    def __init__(self, name, default=None):
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        if not isinstance(name, str):
            raise TypeError(
                'Parameter key must be specified as first argument.'
            )
        self.key = name
        self.default = default

    def execute(self):
        rospy.logdebug(f'executing get_param: {self.key} {self.default}')

    def __str__(self):
        return f'{self.name}: {self.key} {self.default}'

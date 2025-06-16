import json
from json import JSONEncoder
import attr
import rospy

from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton


class ObjectEncoder(JSONEncoder):
    def default(self, o):
        return attr.asdict(o)


class SetParam(Command):
    name = 'set_param'

    def __init__(self, name: str, value: object):
        """
        Sets a user parameter to a the defined value.

        :param name: Parameter name.
        :param value: Value to store.

        .. code-block:: python

            set_param("my_waypoint", waypoint1)
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        if not isinstance(name, str):
            raise TypeError(
                'Parameter key must be specified as first argument.'
            )
        self.key = name
        self.value = value

    def execute(self) -> None:
        rospy.logdebug(f'executing set_param: {self.key} {self.value}')
        if isinstance(self.value, (bool, float, int, str, bytes)):
            value = self.value
        else:
            value = json.dumps(self.value, cls=ObjectEncoder)
        self._config.set_custom_param(self.key, value)

    def __str__(self):
        return f'{self.name}: {self.key} {self.value}'

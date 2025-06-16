from json import JSONEncoder
import attr
import rospy

from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton


class ObjectEncoder(JSONEncoder):
    def default(self, o):
        return attr.asdict(o)


class DeleteParam(Command):
    name = 'delete_param'

    def __init__(self, name: str):
        """
        Removes a user parameter

        :param name: Parameter name to delete

        .. code-block:: python

            delete_param("my_waypoint")
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        if not isinstance(name, str):
            raise TypeError(
                'Parameter key must be specified as first argument.'
            )
        self.key = name

    def execute(self) -> None:
        rospy.logdebug(f'executing delete_param: {self.key}')
        self._config.delete_custom_param(self.key)

    def __str__(self):
        return f'{self.name}: {self.key}'

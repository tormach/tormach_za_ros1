from json import JSONDecoder
from json.decoder import JSONDecodeError

import rospy

from .. import rpl
from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton


class GetParam(Command):
    name = 'get_param'

    def __init__(self, name: str, default: object = None):
        """
        Fetch a stored user parameter.

        :param name: Parameter name.
        :param default: Default value return if the parameter is not defined.
        :return: Returns a base Python type, construct rpl types or returns a dict if the parameter is set,
                 else returns the default value.

        **Examples**

        .. code-block:: python

            wp = get_param("my_waypoint", Pose())
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        if not isinstance(name, str):
            raise TypeError(
                'Parameter key must be specified as first argument.'
            )
        self.key = name
        self.default = default

    def execute(self) -> object:
        rospy.logdebug(f'executing get_param: {self.key} {self.default}')
        data = self._config.get_custom_param(self.key, default=None)
        if data is not None:
            if isinstance(data, str):
                try:
                    return JSONDecoder(object_hook=self._from_json).decode(data)
                except (TypeError, JSONDecodeError):
                    return data
            else:
                return data
        else:
            return self.default

    @staticmethod
    def _from_json(o):
        if "_obj_name" not in o:
            return o
        type_ = o["_obj_name"]
        del o["_obj_name"]
        for name, value in o.items():
            if name[0] == '_':
                del o[name]
                continue
            try:
                if type_ in dir(rpl):
                    return getattr(rpl, type_)(**o)
                else:
                    raise ValueError()
            except (KeyError, ValueError):
                rospy.logerr(f'Error creating object {type_}')
                return None

    def __str__(self):
        return f'{self.name}: {self.key} {self.default}'

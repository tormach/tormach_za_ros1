from typing import Tuple, Union

import rospy

from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton
from .set_units import convert_unit_name


class GetUnits(Command):
    name = 'get_units'

    def __init__(self, with_time: bool = False):
        """
        Returns the active linear, angular and time units from the program.

        :param time: return the time unit type when set to True

        :return: Linear/length unit type, angular/rotation unit type and time unit type

        **Examples**

        .. code-block:: python

            linear, angular = get_units()
            linear, angular, time = get_units(with_time=True)
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()
        self.with_time = with_time

    def execute(self) -> Union[Tuple[str, str], Tuple[str, str, str]]:
        rospy.logdebug(f'executing {self.name}')

        return (
            (
                convert_unit_name(self._config.linear_unit),
                convert_unit_name(self._config.angular_unit),
                convert_unit_name(self._config.time_unit),
            )
            if self.with_time
            else (
                convert_unit_name(self._config.linear_unit),
                convert_unit_name(self._config.angular_unit),
            )
        )

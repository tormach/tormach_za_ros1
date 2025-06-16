from typing import Optional, Union

import rospy
from ..rpl.units import ureg
from pint.util import SharedRegistryObject

from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton


def convert_unit_name(name):
    switch = {
        'meter': 'm',
        'inch': 'in',
        'millimeter': 'mm',
        'degree': 'deg',
        'radian': 'rad',
        'second': 's',
        'minute': 'min',
        'hour': 'h',
    }
    return switch.get(name, name)


class SetUnits(Command):
    name = 'set_units'

    def __init__(
        self,
        linear: Optional[Union[str, SharedRegistryObject]] = None,
        angular: Optional[Union[str, SharedRegistryObject]] = None,
        time: Optional[Union[str, SharedRegistryObject]] = None,
    ):
        """
        Sets the active linear, angular and time units for the program.

        :param linear: Linear/length unit type: m, mm, inch
        :param angular: Angular/rotation unit type: deg, rad
        :param time: Time unit type: s, min, h

        **Examples**

        .. code-block:: python

            set_units("mm", "deg", "s")
            set_units(linear="in")
            set_units(angular="rad")
            set_units(time="s")
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        self.linear_unit = (
            self._check_unit_type(linear) if linear is not None else None
        )
        self.angular_unit = (
            self._check_unit_type(angular, angular=True)
            if angular is not None
            else None
        )
        self.time_unit = (
            self._check_unit_type(time, time=True) if time is not None else None
        )

    def _check_unit_type(self, type_, angular=False, time=False):
        if isinstance(type_, str):
            try:
                unit = ureg.parse_expression(type_)
            except (AttributeError, KeyError) as e:
                raise TypeError(f"Type with name {type_} is not known.") from e
        elif isinstance(type_, SharedRegistryObject):
            unit = type_
        else:
            raise TypeError("Given value is not a supported unit type.")

        if (
            (angular and unit.dimensionality != ureg.rad.dimensionality)
            or (time and unit.dimensionality != ureg.s.dimensionality)
            or (
                not angular
                and not time
                and unit.dimensionality != ureg.m.dimensionality
            )
        ):
            raise TypeError("Dimensionality of given type does not match.")

        return convert_unit_name(str(unit.units))

    def execute(self):
        rospy.logdebug(
            f'executing {self.name}: linear={self.linear_unit}, '
            f'angular={self.angular_unit}, time={self.time_unit}'
        )

        if self.linear_unit:
            self._config.set_param('linear_unit', self.linear_unit)
        if self.angular_unit:
            self._config.set_param('angular_unit', self.angular_unit)
        if self.time_unit:
            self._config.set_param('time_unit', self.time_unit)

    def __str__(self):
        return (
            f'{self.name}: '
            f'{self.linear_unit} {self.angular_unit} {self.time_unit}'
        )

from __future__ import annotations
import numbers

import attr
from pint.util import SharedRegistryObject
from typing import List, Optional, Union

from robot_command.rpl.units import ureg, force_units


class JointsFactory:
    """
    The JointsFactory class helps constructing Joints object using a shorthand
    notation. In the robot program it can be accessed using the ``j[]``
    shortcut or the ``j()`` shortcut which supports keyword arguments.

    **Examples**

    .. code-block:: python

        waypoint_1 = j[0.764, 1.64, 0.741, 0.433, 0.140, 2.74]
        waypoint_2 = j(j3=0.543) # all other joint positions are 0.0 by default
    """

    MESSAGE = 'Exactly 6 values [J1,J2,J3,J4,J5,J6] required to create joint representation.'

    def __getitem__(self, values):
        try:
            elements = len(values)
        except TypeError:
            raise ValueError(self.MESSAGE)
        if elements != 6:
            raise ValueError(self.MESSAGE)
        if not all(isinstance(v, numbers.Number) for v in values):
            raise ValueError(self.MESSAGE)
        return Joints(*values)

    def __call__(self, *args, **kwargs):
        if args and len(args) < 6:
            raise ValueError(
                "Shorthand notation requires at least 6 coordinate values"
                " or keyword arguments only."
            )
        return Joints(*args, **kwargs)


@attr.s(slots=True)
class Joints:
    """
    The Joints object consists of six joint position values to be used as
    target for move commands or to represent the current robot joint state.

    **Examples**

    .. code-block:: python

        waypoint_1 = Joint(323.62, 345.37, 477.76, 431.10, 918.62)
        waypoint_2 = Joint(j3=0.543) # all other joint positions are 0.0 by default
    """

    j1 = attr.ib(default=0.0, type=float)
    j2 = attr.ib(default=0.0, type=float)
    j3 = attr.ib(default=0.0, type=float)
    j4 = attr.ib(default=0.0, type=float)
    j5 = attr.ib(default=0.0, type=float)
    j6 = attr.ib(default=0.0, type=float)
    _obj_name = attr.ib(init=False, default='Joints')

    def copy(self) -> Joints:
        """
        Creates a copy of the joints object.

        :return: Copy of the joints object.
        """
        return attr.evolve(self)

    def to_list(self) -> List[float]:
        """
        Convert the joints object to a list of joint positions.

        :return: List of the six joint positions.
        """
        return [self.j1, self.j2, self.j3, self.j4, self.j5, self.j6]

    @staticmethod
    def from_list(joint_list: List[float]) -> Joints:
        """
        Creates a new joint object from a list of joint positions.

        :param joint_list: List of the six joint positions.
        :return: New joints object.
        """
        return Joints(*joint_list)

    def with_units(
        self, angular_unit: Optional[Union[str, SharedRegistryObject]] = None
    ) -> Joints:
        """
        Adds a unit type to all positions of the joints object. The defaults are
        the native ROS units. In case a joint position already has units, the
        unit type is converted accordingly.

        :param angular_unit: Unit type for the angular joint positions.
        :return: The resulting joints object.
        """
        if angular_unit is None:
            angular_unit = ureg.rad
        return Joints(
            j1=force_units(self.j1, angular_unit),
            j2=force_units(self.j2, angular_unit),
            j3=force_units(self.j3, angular_unit),
            j4=force_units(self.j4, angular_unit),
            j5=force_units(self.j5, angular_unit),
            j6=force_units(self.j6, angular_unit),
        )

    def without_units(
        self, angular_unit: Optional[Union[str, SharedRegistryObject]] = None
    ) -> Joints:
        """
        Removes units from the joint positions if any. If no unit type is
        specified ROS units are assumed.

        :param angular_unit: Unit type for the angular joint positions.
        :return: The resulting joints object.
        """
        if angular_unit is None:
            angular_unit = ureg.rad
        return Joints(
            j1=force_units(self.j1, angular_unit).magnitude,
            j2=force_units(self.j2, angular_unit).magnitude,
            j3=force_units(self.j3, angular_unit).magnitude,
            j4=force_units(self.j4, angular_unit).magnitude,
            j5=force_units(self.j5, angular_unit).magnitude,
            j6=force_units(self.j6, angular_unit).magnitude,
        )

    def to_ros_units(
        self, angular_unit: Optional[Union[str, SharedRegistryObject]] = None
    ) -> Joints:
        """
        Converts the joints object to native ROS units, removing the unit type
        if any. This is useful if you want to send the resulting data to a ROS
        service.

        :param angular_unit: Unit type for the angular joint positions.
        :return: The resulting joints object.
        """
        if angular_unit is None:
            angular_unit = ureg.rad
        return Joints(
            j1=force_units(self.j1, angular_unit).to(ureg.rad).magnitude,
            j2=force_units(self.j2, angular_unit).to(ureg.rad).magnitude,
            j3=force_units(self.j3, angular_unit).to(ureg.rad).magnitude,
            j4=force_units(self.j4, angular_unit).to(ureg.rad).magnitude,
            j5=force_units(self.j5, angular_unit).to(ureg.rad).magnitude,
            j6=force_units(self.j6, angular_unit).to(ureg.rad).magnitude,
        )

    def from_ros_units(
        self, angular_unit: Optional[Union[str, SharedRegistryObject]] = None
    ):
        """
        Converts the joints object from native ROS units to the target units,
        removing the unit type if any.

        :param angular_unit: Unit type for the angular joint positions.
        :return: The resulting joints object.
        """
        if angular_unit is None:
            angular_unit = ureg.rad
        return Joints(
            j1=force_units(self.j1, ureg.rad).to(angular_unit).magnitude,
            j2=force_units(self.j2, ureg.rad).to(angular_unit).magnitude,
            j3=force_units(self.j3, ureg.rad).to(angular_unit).magnitude,
            j4=force_units(self.j4, ureg.rad).to(angular_unit).magnitude,
            j5=force_units(self.j5, ureg.rad).to(angular_unit).magnitude,
            j6=force_units(self.j6, ureg.rad).to(angular_unit).magnitude,
        )

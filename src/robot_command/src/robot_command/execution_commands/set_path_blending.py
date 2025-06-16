from typing import Optional

import rospy

from ..rpl import Command
from ..interfaces import ConfigInterfaceSingleton
from ..rpl.units import ureg, force_units


class SetPathBlending(Command):
    name = 'set_path_blending'

    def __init__(self, enable: bool, blend_radius: Optional[float] = None):
        """
        Enables or disables path blending and sets the blend radius.

        :param enable: Enable or disable path blending.
        :param blend_radius: The blend radius between moves in meters.

        **Examples**

        .. code-block:: python

            set_path_blending(True, 0.0)  # enable path blending, blend radius 0.0m
            movej(waypoint1)
            movej(waypoint2)
            movej(waypoint3)
            sync()  # moves executed before this command
            set_path_blending(False)  # disable path blending again
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        if blend_radius is not None:
            if not isinstance(blend_radius, (float, int, ureg.Quantity)):
                raise TypeError(
                    f"{self.name} requires a numeric value as blend radius argument."
                )
            blend_radius = (
                force_units(blend_radius, self._config.linear_unit)
                .to(ureg.m)
                .magnitude
            )
            if blend_radius < 0.0:
                raise ValueError("The blend radius must be a positive value.")

        self.enable = bool(enable)
        self.blend_radius = blend_radius

    def execute(self) -> None:
        rospy.logdebug(
            f"executing {self.name}: enable={self.enable}, "
            f"blend_radius={self.blend_radius}"
        )

        if self.blend_radius is not None:
            self._config.set_param('blend_radius', self.blend_radius)
        self.interpreter.async_enabled = self.enable

    def __str__(self):
        return f'{self.name}: {self.enable} {self.blend_radius}'

import rospy

from ..rpl import Command


class SetPathBlending(Command):
    name = 'set_path_blending'

    def __init__(self, enable, blend_radius=None):
        super().__init__()

        self.enable = bool(enable)
        self.blend_radius = blend_radius

    def execute(self):
        rospy.logdebug(
            f"executing {self.name}: enable={self.enable}, "
            f"blend_radius={self.blend_radius}"
        )

        self.interpreter.async_enabled = self.enable

    def __str__(self):
        return f'{self.name}: {self.enable} {self.blend_radius}'

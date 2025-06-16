from ..rpl import Command
from ..interfaces import AllowedConfigurationsInterfaceSingleton

from movej_ik_server.arm_configs import JointConfig

import rospy


class AllowedConfigurations(Command):
    name = 'allowed_configurations'
    ALLOWED_CONFIGURATIONS_INTERFACE = AllowedConfigurationsInterfaceSingleton

    def __init__(self, config_mask_object):
        super().__init__()

        if isinstance(config_mask_object, JointConfig):
            self.config_mask = config_mask_object.value
        else:
            raise TypeError("Argument must be JointConfig")

        self._interface = self.ALLOWED_CONFIGURATIONS_INTERFACE()

    def execute(self) -> None:
        self._interface.set_allowed_constraints(self.config_mask)
        rospy.loginfo(f'Allowed configurations set to {self.config_mask}')

    def __str__(self):
        return f'{self.name}: {self.config_mask}'

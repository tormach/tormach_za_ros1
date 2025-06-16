import rospy


from ..rpl import Command
from ..interfaces import MachinetalkInterfaceSingleton
from ..interfaces.machinetalk_interface import (
    MachinetalkInstanceNotConnectedError,
    MachinetalkInstanceNotFoundError,
)
from ..rpl.exceptions import (
    PathPilotInstanceNotConnectedError,
    PathPilotInstanceNotFoundError,
)


class PathPilotCycleStart(Command):
    name = 'pathpilot_cycle_start'

    def __init__(self, instance: str = ''):
        """
        Starts a cycle on the remote PathPilot instance. If no instance argument is
        given, the command is executed on the first connected PathPilot instance.

        :param instance: PathPilot instance on which cycle start should be executed.

        **Examples**

        .. code-block:: python

            pathpilot_cycle_start()
            pathpilot_cycle_start("left_mill")
        """
        super().__init__()
        self._machinetalk = MachinetalkInterfaceSingleton()

        if isinstance(instance, str):
            self.instance = instance
        else:
            raise TypeError('Optional instance parameter must be a string.')

    def execute(self) -> None:
        rospy.logdebug(
            f'executing pathpilot_cycle_start: instance={self.instance}'
        )
        try:
            self._machinetalk.cycle_start(instance=self.instance)
        except MachinetalkInstanceNotConnectedError as e:
            raise PathPilotInstanceNotConnectedError(
                f'PathPilot instance {e.instance} is not connected.',
                e.instance,
            )
        except MachinetalkInstanceNotFoundError as e:
            raise PathPilotInstanceNotFoundError(
                f'PathPilot instance {e.instance} could not be found.',
                e.instance,
            )

    def __str__(self):
        return f'{self.name}: {self.instance}'

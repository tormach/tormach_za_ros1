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


class PathPilotMdi(Command):
    name = 'pathpilot_mdi'

    def __init__(self, command: str, instance: str = ''):
        """
        Starts an MDI command on the remote PathPilot instance. If no instance
        argument is given, the command is executed on the first connected PathPilot
        instance.

        :param command: MDI command to execute.
        :param instance: PathPilot instance on which this command shall be executed.

        **Examples**

        .. code-block:: python

            pathpilot_mdi("G0 X10")
            pathpilot_mdi("G1 Y-5 F300", "right_mill")
        """
        super().__init__()
        self._machinetalk = MachinetalkInterfaceSingleton()

        if isinstance(command, str):
            self.command = command
        else:
            raise TypeError('MDI command must be specified as first argument.')

        if isinstance(instance, str):
            self.instance = instance
        else:
            raise TypeError('Optional instance parameter must be a string.')

    def execute(self) -> None:
        rospy.logdebug(
            'executing pathpilot_mdi: cmd={}, instance={}'.format(
                self.command, self.instance
            )
        )
        try:
            self._machinetalk.execute_mdi(
                command=self.command, instance=self.instance
            )
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
        return f'{self.name}: {self.command} {self.instance}'

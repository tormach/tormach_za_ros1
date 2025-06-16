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


class PathPilotAbort(Command):
    name = 'pathpilot_abort'

    def __init__(self, instance: str = ''):
        """
        Aborts any running command on the remote PathPilot instance. If no
        instance argument is given, the command is executed on the first
        connected PathPilot instance.

        :param instance: PathPilot instance on which abort should be executed.

        **Examples**

        .. code-block:: python

            pathpilot_abort()
            pathpilot_abort("left_mill")
        """
        super().__init__()
        self._machinetalk = MachinetalkInterfaceSingleton()

        if isinstance(instance, str):
            self.instance = instance
        else:
            raise TypeError('Optional instance parameter must be a string.')

    def execute(self) -> None:
        rospy.logdebug(f'executing pathpilot_abort: instance={self.instance}')
        try:
            self._machinetalk.abort(instance=self.instance)
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

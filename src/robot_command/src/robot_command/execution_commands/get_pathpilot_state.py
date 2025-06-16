import rospy

from ..rpl import Command
from ..interfaces import MachinetalkInterfaceSingleton


class GetPathPilotState(Command):
    name = 'get_pathpilot_state'

    def __init__(self, instance: str = ""):
        """
        Returns the current state of a PathPilot instance. If no instance argument
        is given, the command is executed on the first connected PathPilot instance.

        Possible states are:

        * “disconnected” - Instance disconnected
        * “estop” - Emergency stop active
        * “running” - a program is running
        * “ready” - instance is ready to start program
        * “idle” - instance is idle, no program loaded

        :param instance: PathPilot instance on which cycle start should be executed.
        :return: The current PathPilot state.

        **Examples**

        .. code-block:: python

            state = get_pathpilot_instance()
            while get_pathpilot_instance("left_mill") != "ready":
                sleep(0.1)
        """
        super().__init__()
        self._machinetalk = MachinetalkInterfaceSingleton()

        if isinstance(instance, str):
            self.instance = instance
        else:
            raise TypeError('Optional instance parameter must be a string.')

    def execute(self) -> str:
        rospy.logdebug(
            f'executing get_pathpilot_state: instance={self.instance}'
        )
        return self._machinetalk.get_machine_state(instance=self.instance)

    def __str__(self):
        return f'{self.name}: {self.instance}'

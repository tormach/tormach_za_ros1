import rospy

from ..interfaces import ConfigInterfaceSingleton
from ..program_interpreter import InterpreterProcess
from ..rpl import Command


class Pause(Command):
    name = 'pause'

    def __init__(self, optional: bool = False, active: bool = False):
        """
        The pause command pauses the program execution. Equivalent to M01 break.

        The ``optional`` states whether the pause is optional or not. Optional pause
        can be enabled in the robot UI by the operator.

        :param optional: If this pause is optional or not.
        :param active: When set to true, this indicates an active pause allowing to operator to jog the program.

        **Examples**

        .. code-block:: python

            pause()
            pause(optional=True)
        """
        super().__init__()
        self._config = ConfigInterfaceSingleton()

        self.optional = bool(optional)
        self.active = bool(active)

    def execute(self) -> None:
        rospy.logdebug(
            f'executing pause: optional={self.optional} active={self.active}'
        )

        if self.optional and not self._config.optional_stop:
            return

        InterpreterProcess.pause_command(
            active=self.active, reason="Program pause() command"
        )

    def __str__(self):
        return f'{self.name}: optional={self.optional} active={self.active}'

import time

import rospy

from ..execution_commands.constants import SYNC_TIME
from ..program_interpreter import InterpreterProcess
from ..program_interpreter.interpreter import ProgramPause
from ..rpl import Command


class Sleep(Command):
    name = 'sleep'

    def __init__(self, secs: float):
        """
        The sleep command pauses the program execution for ``t`` seconds.

        :param secs: sleep time in seconds

        **Examples**

        .. code-block:: python

            sleep(5.0)
        """
        super().__init__()

        if not isinstance(secs, (float, int)) or secs < 0:
            raise TypeError(
                'Sleep requires a positive number as secs argument.'
            )

        self.secs = secs

    def execute(self) -> None:
        rospy.logdebug(f'executing sleep: {self.secs}s')

        wait_time_s = self.secs
        while InterpreterProcess.spin_pause():
            start_time = time.time()
            try:
                while InterpreterProcess.spin_command():
                    current_time = time.time()
                    delta = current_time - start_time
                    if delta >= wait_time_s:
                        return
                    rospy.sleep(SYNC_TIME)
            except ProgramPause as e:
                current_time = time.time()
                delta = current_time - start_time
                wait_time_s = wait_time_s - delta
                rospy.loginfo(f'Paused executing sleep:  {e}')

    def __str__(self):
        return f'{self.name}: {self.secs}'

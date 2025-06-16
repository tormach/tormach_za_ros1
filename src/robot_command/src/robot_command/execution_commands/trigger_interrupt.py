from typing import Any

import rospy

from ..interfaces import InterruptInterfaceSingleton
from ..rpl import Command


class TriggerInterrupt(Command):
    name = 'trigger_interrupt'

    def __init__(self, nr: int, value: Any):
        """
        Triggers a program interrupt.

        :param nr: Program interrupt number which should be triggered.
        :param value: Value which is passed along with the triggered interrupt.

        **Examples**

        .. code-block:: python

            trigger_interrupt(2, 342.34)
        """
        super().__init__()
        self._interrupts = InterruptInterfaceSingleton()

        if not isinstance(nr, int) or nr < 1:
            raise ValueError("Program interrupt number must be >= 1.")

        self.nr = nr
        self.value = value

    def execute(self) -> None:
        rospy.logdebug(f"executing {self.name}: {self.nr} {self.value}")
        self._interrupts.trigger_program_interrupt(self.nr, self.value)

    def __str__(self):
        return f'{self.name}: {self.nr} {self.value}'

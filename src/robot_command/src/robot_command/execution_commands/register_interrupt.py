from typing import Union, Callable

import rospy

from ..rpl import Command, InterruptSource
from ..interfaces import HalIoInterfaceSingleton, InterruptInterfaceSingleton


class RegisterInterrupt(Command):
    name = 'register_interrupt'

    def __init__(
        self,
        source: InterruptSource,
        nr_or_name: Union[int, str],
        fct: Callable,
    ):
        """
        Registers a interrupt function to an interrupt source.

        :param source: The interrupt source type.
        :param nr_or_name: Number or name of the interrupt source, e.g. 1 for Digital Input 1.
        :param fct: The function which should be called when the interrupt is triggered,
            if None is passed, this unregisters and disables the interrupt.

        **Examples**

        .. code-block:: python

            def interrupt_handler(value):
                if value:
                    exit() # exit program when digital input 1 is high

            register_interrupt(InterruptSource.DigitalInput, 1, interrupt_handler)
        """
        super().__init__()
        self._interrupts = InterruptInterfaceSingleton()
        self._hal_io = HalIoInterfaceSingleton()

        # check source type
        if source == InterruptSource.DigitalInput:
            if isinstance(nr_or_name, str):
                nr = self._get_digital_input_nr_for_name(nr_or_name)
            elif isinstance(nr_or_name, int):
                self._check_if_digital_input_nr_is_in_range(nr_or_name)
                nr = nr_or_name
            else:
                raise TypeError(
                    "Pin number or name must be specified as second argument."
                )
        elif source == InterruptSource.UserIo:
            if not isinstance(nr_or_name, int):
                raise TypeError(
                    "Interrupt number must be specified as second argument."
                )
            self._check_if_user_io_number_is_in_range(nr_or_name)
            nr = nr_or_name
        elif source == InterruptSource.Program:
            if not isinstance(nr_or_name, int):
                raise TypeError(
                    "Interrupt number must be specified as second argument."
                )
            if nr_or_name < 1:
                raise ValueError("Program interrupt number must be >= 1.")
            nr = nr_or_name
        else:
            raise TypeError("")

        self.source = source
        self.nr = nr
        self.fct = fct

    def _get_digital_input_nr_for_name(self, name):
        nr = self._hal_io.get_digital_input_nr(name)
        if nr == -1:
            raise KeyError(f"No digital input pin named {name}")
        return nr

    def _check_if_digital_input_nr_is_in_range(self, nr):
        io_count = self._hal_io.digital_in_count
        if not 0 < nr <= io_count:
            raise ValueError(
                "Digital input pin number must be in range 1-{}".format(
                    io_count
                )
            )

    def _check_if_user_io_number_is_in_range(self, nr):
        io_count = self._hal_io.user_io_count
        if not 0 < nr <= io_count:
            raise ValueError(f"User IO pin must be in range 1-{io_count}")

    def execute(self) -> None:
        rospy.logdebug(f"executing {self.name}: {self.source} {self.nr}")
        if self.fct is None:
            self._interrupts.unregister_interrupt(self.source, self.nr)
        else:
            self._interrupts.register_interrupt(self.source, self.nr, self.fct)

    def __str__(self):
        return f'{self.name}: {self.source} {self.nr}'

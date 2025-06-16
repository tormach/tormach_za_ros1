from typing import Union

import rospy

from ..rpl import Command
from ..interfaces import HalIoInterfaceSingleton


class SetDigitalOut(Command):
    name = 'set_digital_out'

    def __init__(self, nr_or_name: Union[int, str], state: bool):
        """
        Sets a digital output pin to high or low state.

        :param nr_or_name: The number or name of the digital output pin.
        :param state: Set to True or False for on and off.

        **Examples**

        .. code-block:: python

            set_digital_out("gripper", True)
            set_digital_out(2, False)
        """
        super().__init__()
        self._hal_io = HalIoInterfaceSingleton()

        if isinstance(nr_or_name, str):
            nr = self._get_nr_for_name(nr_or_name)
        elif isinstance(nr_or_name, int):
            self._check_if_nr_is_in_range(nr_or_name)
            nr = nr_or_name
        else:
            raise TypeError(
                'Pin number or name must be specified as first argument.'
            )

        self.nr = nr
        self.state = state

    def _get_nr_for_name(self, name):
        nr = self._hal_io.get_digital_output_nr(name)
        if nr == -1:
            raise KeyError(f'No digital output pin named {name}')
        return nr

    def _check_if_nr_is_in_range(self, nr):
        io_count = self._hal_io.digital_out_count
        if not 0 < nr <= io_count:
            raise ValueError(
                'Digital output pin number must be in range 1-{}'.format(
                    io_count
                )
            )

    def execute(self) -> None:
        rospy.logdebug(f'executing set_digital_out: {self.nr} {self.state}')
        self._hal_io.set_digital_output(self.nr, self.state)

    def __str__(self):
        return f'{self.name}: {self.nr} {self.state}'

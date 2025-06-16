from typing import Union

import rospy

from ..rpl import Command
from ..interfaces import HalIoInterfaceSingleton


class GetDigitalIn(Command):
    name = 'get_digital_in'

    def __init__(self, nr_or_name: Union[str, int]):
        """
        Returns the current digital input state.

        :param nr_or_name: The number or name of the digital output pin.
        :return: True or False for High and Low.

        **Examples**

        .. code-block:: python

            io_state = get_digital_in("gripper")
            x = get_digital_in(3)
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

    def _get_nr_for_name(self, name):
        nr = self._hal_io.get_digital_input_nr(name)
        if nr == -1:
            raise KeyError(f'No digital input pin named {name}')
        return nr

    def _check_if_nr_is_in_range(self, nr):
        io_count = self._hal_io.digital_in_count
        if not 0 < nr <= io_count:
            raise ValueError(
                'Digital input pin number must be in range 1-{}'.format(
                    io_count
                )
            )

    def execute(self) -> bool:
        rospy.logdebug(f'executing get_digital_in: {self.nr}')
        return self._hal_io.get_digital_input(self.nr)

    def __str__(self):
        return f'{self.name}: {self.nr}'

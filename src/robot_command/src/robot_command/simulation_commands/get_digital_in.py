import time

from ..rpl import Command
from .constants import SLEEP_TIME


class GetDigitalIn(Command):
    name = 'get_digital_in'

    def __init__(self, n):
        super().__init__()
        self.n = n

    def execute(self):
        print(f'executing get_digital_in: {self.n}')
        time.sleep(SLEEP_TIME)
        return True

    def __str__(self):
        return f'{self.name}: {self.n}'

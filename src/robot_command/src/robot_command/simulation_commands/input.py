import time

from ..rpl import Command
from .constants import SLEEP_TIME


class Input(Command):
    name = 'input'

    def __init__(self, message, default='', image_path=''):
        super().__init__()

        if not isinstance(message, str):
            raise TypeError('Message text must be specified as first argument.')

        self.message = message
        self.default = default
        self.image_path = image_path

    def execute(self):
        print('executing input')
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return '{}: "{}" {} "{}"'.format(
            self.name, self.message, self.default, self.image_path
        )

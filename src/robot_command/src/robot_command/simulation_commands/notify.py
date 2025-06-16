import os

import time

from ..rpl import Command
from .constants import SLEEP_TIME


class Notify(Command):
    name = 'notify'

    def __init__(self, message, warning=False, error=False, image_path=''):
        super().__init__()
        self.message = message
        self.warning = warning
        self.error = error
        self.image_path = os.path.abspath(os.path.expanduser(image_path))

    def _type_string(self):
        if self.error:
            return "error"
        elif self.warning:
            return "warning"
        else:
            return "notification"

    def execute(self):
        print('executing notify')
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return '{}: {} "{}" "{}"'.format(
            self.name, self._type_string(), self.message, self.image_path
        )

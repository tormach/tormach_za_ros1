import time

from .constants import SLEEP_TIME
from .move import Move


class MoveF(Move):
    name = 'movef'

    def __init__(self, target, a=0.5, v=0.5):
        super().__init__()
        self.target = self._check_target(target)
        self._check_move_params(a, v)
        self.a = a
        self.v = v

    def execute(self):
        print(f'executing {self.name} command: {self.target}')
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return f'{self.name}: {self.target}'

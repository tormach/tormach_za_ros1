import time

from .constants import SLEEP_TIME
from .move import Move


class MoveJ(Move):
    name = 'movej'

    def __init__(self, target, v=None, probe=0, velocity_scale=1.0):
        super().__init__()
        self.target = self._check_target(target)
        self._check_move_params(1.0, v)
        self.probe = probe
        self.velocity_scale = velocity_scale

    def execute(self):
        print(f'executing movej command: {self.target}')
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return f'{self.name}: {self.target}'

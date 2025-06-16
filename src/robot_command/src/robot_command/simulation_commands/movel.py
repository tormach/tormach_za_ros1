import time

from .constants import SLEEP_TIME
from .move import Move


class MoveL(Move):
    name = 'movel'

    def __init__(
        self,
        target,
        a=None,
        v=None,
        probe=0,
        velocity=None,
        accel=None,
        accel_scale=0.5,
        duration=0,
        strict_limits=False,
    ):
        super().__init__()
        self.target = self._check_target(target)
        self._check_move_params(a, v)
        self.probe = probe
        self.velocity = velocity
        self.accel = accel
        self.accel_scale = accel_scale
        self.duration = duration
        self.strict_limits = strict_limits

    def execute(self):
        print('executing movel command')
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return f'{self.name}: {self.target}'

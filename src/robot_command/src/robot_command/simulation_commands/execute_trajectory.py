import time

from .constants import SLEEP_TIME
from ..rpl import Command


class ExecuteTrajectory(Command):
    name = 'execute_trajectory'

    def __init__(
        self,
        trajectory,
        v: float = None,
        retime: bool = False,
        velocity_scale: float = 1.0,
    ):
        super().__init__()

        self.trajectory = trajectory
        self.velocity_scale = velocity_scale
        self.retime = retime

    def execute(self):
        print(
            f'executing execute trajectory command: {len(self.trajectory.points)} waypoints'
        )
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return (
            f'{self.name}: total points={len(self.trajectory.points)} '
            f'v={self.velocity_scale} retime={self.retime}'
        )

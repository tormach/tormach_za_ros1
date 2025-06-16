import time
from typing import Union, Optional
from pint import Quantity

from ..rpl import Pose, Joints
from .constants import SLEEP_TIME
from .move import Move


class ProbeCycle(Move):
    name = 'probel'

    def __init__(
        self,
        target: Union[Pose, Joints, str],
        accel_scale: float = 0.5,
        accel: Optional[Union[float, Quantity]] = None,
        velocity_probe: float = 0.1,
        velocity_retract: float = 0.1,
        away: bool = False,
        check_retract_contact: bool = False,
        strict_limits: bool = False,
        # Deprecated arguments last
        a: float = None,
        v: float = None,
        v_retract: float = None,
    ) -> Pose:
        super().__init__()
        self.retract_mode = 6 if check_retract_contact else 7
        self._check_move_params(1.0, v or 1.0)
        self._check_move_params(1.0, a or 1.0)
        self._check_move_params(1.0, accel_scale or 1.0)

        self.v = v
        self.a = a
        self.accel = accel
        self.accel_scale = accel_scale
        self.velocity_probe = velocity_probe
        self.velocity_retract = velocity_retract
        self.strict_limits = strict_limits
        self.v_retract = v_retract or v
        self.probe_target = target
        self.away = away

    def execute(self):
        print(f'executing probel command: {self.probe_target}')
        time.sleep(SLEEP_TIME)

    def __str__(self):
        return f'{self.name}: {self.probe_target}'

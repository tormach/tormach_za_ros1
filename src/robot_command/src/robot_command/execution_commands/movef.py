from typing import Union

import rospy

from ..program_interpreter import InterpreterProcess  # noqa: F401
from ..program_interpreter.interpreter import (  # noqa: F401
    ProgramPause,
    ProgramUpdate,
)
from ..rpl import Pose, Joints

from .move_commands import MoveCommand
from ..rpl.command import Command


class MoveF(Command, MoveCommand):
    name = 'movef'

    def __init__(self, target: Union[Pose, Joints]):
        """
        Free move command.

        :param target: target target
        """
        Command.__init__(self)
        MoveCommand.__init__(self)

        self.target = self._check_target(target)

    def execute(self) -> None:
        rospy.logdebug(f'executing {self.name} command: {self.target}')

        target = self._resolve_waypoint(self.target)

        if isinstance(target, Pose):
            self._check_pose_frame(target)
            target = self._apply_frames_to_pose(
                target.to_ros_units(
                    self._config.linear_unit, self._config.angular_unit
                )
            )
        else:
            target = target.to_ros_units(self._config.angular_unit).to_list()

        plan = None
        if self._target_is_current(target):
            return
        self._update_vel_accel(
            accel_scale=1.0, velocity_scale=1.0, use_feedrate=False
        )
        if plan:
            plan = self._moveit.recompute_trajectory(
                plan,
                self._final_accel_scale,
                self._final_velocity_scale,
            )
        else:
            plan = self._plan_and_wait(target, self._moveit.FREE_MOVE_PLANNER)
        self._execute_and_wait(plan)

    def __str__(self):
        return f'{self.name}: {self.target}'

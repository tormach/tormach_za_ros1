from typing import Union, Tuple

import rospy

from ..program_interpreter import InterpreterProcess  # noqa: F401
from ..program_interpreter.interpreter import (  # noqa: F401
    ProgramPause,
    ProgramUpdate,
)  # noqa: F401
from ..rpl import Pose, AsyncCommand, Joints

from .move_commands import MoveCommand


class MoveJ(AsyncCommand, MoveCommand):
    name = 'movej'

    def __init__(
        self,
        target: Union[Pose, Joints],
        v: float = None,
        probe: int = 0,
        velocity_scale: float = 1.0,
    ):
        """

        Moves the robot end effector to the target waypoint with a joints move.
        Targets can be local waypoints or global waypoints defined as pose or
        joints.

        :param target: target waypoint or joints target
        :param velocity_scale: scale factor for velocity (default is full speed)
        :param probe: specify the probe mode (2-6, or 0 for no probing)
            Probe mode 2: look for rising edge on probe signal (i.e. contact), raise ProbeFailedError if move completes without seeing a rising edge
            Probe mode 3: like mode 2 but does not raise error if move completes without rising edge
            Probe mode 4: like mode 2 but looks for falling edge
            Probe mode 5: like mode 4 but does not raise an error if move completes without falling edge
            Probe mode 6: "retract" mode, ignore falling edges and allow motion while probe signal is active, but raise ProbeUnexpectedContactError if a rising edge is seen

        :return: tuple of probe results (for probing mode 2,3,4,5) or None:
            (probe contact type (0 = no contact, 1 = rising, 2 = falling),
            time of probe contact,
            Joint positions at probe contact,
            End-effector position / orientation pose at probe contact)

        :param v: scale factor for velocity (default is full speed)

            .. deprecated:: 3.1.1
                use velocity_scale instead

        **Examples**

        .. code-block:: python

            movej(waypoint_1)
            movej("global_waypoint_1", velocity_scale=0.6)
            movej(p[0, 100, 0, 90, 20, 0])
        """
        AsyncCommand.__init__(self)
        MoveCommand.__init__(self)
        if v is not None:
            rospy.logwarn(
                "Argument \"v\" is deprecated, "
                "use \"velocity_scale\" argument instead."
            )
            velocity_scale = v

        self.target = self._check_target(target)
        self.velocity_scale, _, _ = self._check_vel_accel_params(velocity_scale)
        self._probe_mode = probe

    def is_similar(self, other):
        return other.name == 'movej'

    def execute(
        self, sequence=None, last=False
    ) -> Union[Tuple[int, rospy.Time, Joints, Pose], None]:
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

        if sequence is not None:
            sequence.append(
                self._moveit.create_sequence_item(
                    target, **self._moveit.PTP_MOVE_PLANNER
                )
            )

        plan = None
        self._update_vel_accel(
            accel_scale=1.0,
            velocity_scale=self.velocity_scale,
            use_feedrate=False,
        )
        if sequence is not None:
            if last:
                self._moveit.blend_radius = self._config.blend_radius
                plan = self._plan_sequence(sequence)
        else:
            plan = self._plan_and_wait(target, self._moveit.PTP_MOVE_PLANNER)
        if plan:
            self._execute_and_wait(plan)
        return self._move_result

    def __str__(self):
        return f'{self.name}: {self.target}'

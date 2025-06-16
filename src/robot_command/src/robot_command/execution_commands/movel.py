from typing import Union, Tuple, Optional

import rospy
from pint import Quantity

from ..program_interpreter import InterpreterProcess  # noqa: F401
from ..program_interpreter.interpreter import (  # noqa: F401
    ProgramPause,
    ProgramUpdate,
)
from ..rpl import Pose, AsyncCommand, Joints

from .move_commands import MoveCommand


class MoveL(AsyncCommand, MoveCommand):
    name = 'movel'

    def __init__(
        self,
        target: Union[Pose, Joints],
        a: float = None,
        v: float = None,
        probe: int = 0,
        velocity: Optional[Union[float, Quantity]] = None,
        accel: Optional[Union[float, Quantity]] = None,
        accel_scale: float = 0.5,
        duration: Optional[Union[float, Quantity]] = None,
        strict_limits: bool = False,
    ):
        """
        Moves the robot end effector in a straight line from the current position to
        the target waypoint. Targets can be local waypoints or global waypoints
        defined as pose or joints.

        :param target: target waypoint
        :param probe: specify the probe mode (2-6, or 0 for no probing)
            Probe mode 2: look for rising edge on probe signal (i.e. contact), raise ProbeFailedError if move completes without seeing a rising edge
            Probe mode 3: like mode 2 but does not raise error if move completes without rising edge
            Probe mode 4: like mode 2 but looks for falling edge
            Probe mode 5: like mode 4 but does not raise an error if move completes without falling edge
            Probe mode 6: "retract" mode, ignore falling edges and allow motion while probe signal is active, but raise ProbeUnexpectedContactError if a rising edge is seen
        :param velocity: move velocity as absolute value, interpreted
            in terms of currently set machine units if quantity without units is given.
        :param accel: move acceleration as absolute value, interpreted
            in terms of currently set machine units if quantity without units is given.
        :param accel_scale: move acceleration scaling factor 0.0 - 1.0
        :param duration: target move duration in seconds. If move duration based on
            other inputs is longer, the planned duration will be used.
        :param strict_limits: Enforces strict limits. Moves violating
            the velocity and acceleration limits will error.

        :return: tuple of probe results:
            (probe contact type (0 = no contact, 1 = rising, 2 = falling),
            time of probe contact,
            Joint positions at probe contact,
            End-effector position / orientation pose at probe contact)

        :param v: move velocity scaling factor 0.0 - 1.0

            .. deprecated:: 3.1.1
                use velocity instead

        :param a: move acceleration scaling factor 0.0 - 1.0

            .. deprecated:: 3.1.1
                use accel_scale instead

        **Examples**

        .. code-block:: python

            movel(waypoint_1)
            movel("global_waypoint_1", velocity=100)
            movel(j[0.764, 1.64, 0.741, 0.433, 0.140, 2.74])
        """
        AsyncCommand.__init__(self)
        MoveCommand.__init__(self)

        self.target = self._check_target(target)
        velocity_scale = 0.5
        if v is not None:
            rospy.logwarn(
                "Argument \"v\" is deprecated, "
                "use \"velocity\" argument instead."
            )
            velocity_scale = v
        if a is not None:
            rospy.logwarn(
                "Argument \"a\" is deprecated, please \"accel_scale\" "
                "or \"accel\"argument instead."
            )
            accel_scale = a
        (
            self.velocity_scale,
            self.accel_scale,
            self.duration,
        ) = self._check_vel_accel_params(
            velocity_scale, accel_scale, accel, velocity, duration
        )
        self._check_other_params(strict_limits)
        self.strict_limits = strict_limits
        self._probe_mode = probe

    def is_similar(self, other):
        return (
            other.name in ('movec', 'movel')
            and other.accel_scale == self.accel_scale
            and other.velocity_scale == self.velocity_scale
            and other.strict_limits == self.strict_limits
        )

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
                    target,
                    **self._moveit.LIN_MOVE_PLANNER,
                    duration=self.duration,
                )
            )
        plan = None

        self._update_vel_accel(self.accel_scale, self.velocity_scale)
        if sequence is not None:
            if last:
                self._moveit.blend_radius = self._config.blend_radius
                plan = self._plan_sequence(sequence)
        else:
            plan = self._plan_and_wait(
                target,
                self._moveit.LIN_MOVE_PLANNER,
                duration=self.duration,
            )
        if plan:
            self._execute_and_wait(plan)

        return self._move_result

    def __str__(self):
        return f'{self.name}: {self.target}'

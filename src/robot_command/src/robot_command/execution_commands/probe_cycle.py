from typing import Union, Optional
from pint import Quantity

from ..rpl import Pose, Joints
from . import MoveL, GetPose
from ..rpl.command import Command
from ..rpl import ProbeFailedError, ProbeError
import rospy


class ProbeCycle(Command):
    name = 'probel'

    def __init__(
        self,
        target: Union[Pose, Joints, str],
        accel: Optional[Union[float, Quantity]] = None,
        velocity_probe: float = None,
        velocity_retract: float = None,
        away: bool = False,
        check_retract_contact: bool = False,
        strict_limits: bool = False,
        # Deprecated arguments last
        accel_scale: float = 0.5,
        a: float = None,
        v: float = 0.02,
        v_retract: float = 0.05,
    ) -> Pose:
        """
        Simple probing cycle that returns to the initial pose (regardless of the
        probe result). The sequence is:

        1) Linear move at specified vel / accel scale towards the target position
        2) Stop at probe contact, error condition, or motion end
        3) Retract to original position
        4) Raise any errors from the cycle, or return the probe result

        :param target: end point of probing motion (probe cycle uses movel internally)
        :param v: move velocity scaling factor 0.0 - 1.0
        :param a: move acceleration scaling factor 0.0 - 1.0
        :param v_retract: velocity scaling factor to use during retract phase
        :param away: Probe towards work (default) if False, otherwise probe away from work
        :param check_retract_contact: Optionally check for contacts during
            retract move (to avoid retracting into an obstacle and breaking a probe tip)

        .. note:: assumes mode 2/4 for probing, meaning an error will be thrown if it reaches the end without contact.
            Caller can catch this exception if they want mode 3/5 functionality

        **Examples**

        .. code-block:: python

            contact_pose = probel(probe_goal_pose, a=0.5, v=0.01, v_retract=0.1, away=False, check_retract_contact=False)

        """
        super().__init__()

        # TODO use enums instead of hard-coded values for probe mode
        probe_mode = 4 if away else 2
        self.retract_mode = 6 if check_retract_contact else 7
        # Prefer explicit velocity / acceleration values if provided
        self.velocity_probe = velocity_probe
        self.velocity_retract = velocity_retract or velocity_probe
        self.accel = accel

        self.accel_scale = (accel_scale or a) if accel is None else None
        self.v_probe_scale = v if velocity_probe is None else None
        self.v_retract_scale = (
            (v_retract or v)
            if not (velocity_retract or velocity_probe)
            else None
        )
        self.probe_target = target
        self.strict_limits = strict_limits
        # Now prepare probe command from current pose
        self.get_pose_cmd = GetPose()
        self.probe_cmd = MoveL(
            target=target,
            accel_scale=self.accel_scale,
            accel=self.accel,
            v=self.v_probe_scale,
            probe=probe_mode,
            velocity=self.velocity_probe,
            strict_limits=self.strict_limits,
        )

    def execute(self) -> Pose:
        retract_pose = self.get_pose_cmd.execute()
        probe_result = None
        probe_error = None
        try:
            rospy.loginfo(f"Going to probe pose {self.probe_target}")
            probe_result = self.probe_cmd.execute()
        except ProbeError as e:
            probe_error = e
            # Will rethrow later, but if anything else goes wrong, do not try to issue any additional motions

        rospy.loginfo(f"Going to retract_pose {retract_pose}")
        retract_cmd = MoveL(
            target=retract_pose,
            accel=self.accel,
            accel_scale=self.accel_scale,
            v=self.v_retract_scale,
            velocity=self.velocity_retract,
            probe=self.retract_mode,
            strict_limits=self.strict_limits,
        )
        retract_cmd.execute()
        if probe_error:
            raise probe_error
        elif not probe_result or not probe_result[3]:
            raise ProbeFailedError(
                "Probe move failed to capture contact position"
            )

        return probe_result[3]

    def __str__(self):
        return f'probe_cycle from to target {self.probe_target}'

from typing import Union
import rospy

from tf2_geometry_msgs import transform_to_kdl

from stop_event_msgs.srv import GetJointTrajectoryErrorContextResponse as ECResp

from ..execution_commands.constants import SYNC_TIME
from ..program_interpreter import InterpreterProcess, ProgramExit
from ..program_interpreter.interpreter import ProgramPause
from ..rpl import (
    Pose,
    Joints,
    MovePlanningError,
    PathToleranceError,
    GoalToleranceError,
    ProbeUnexpectedContactError,
    ProbeContactAtStartError,
    ProbeFailedError,
    MoveExecutionError,
)
from ..interfaces import (
    UserFrameInterfaceSingleton,
    GlobalWaypointInterfaceSingleton,
    MoveItInterfaceSingleton,
    JointsToPoseInterfaceSingleton,
    ConfigInterfaceSingleton,
    ToolFrameInterfaceSingleton,
    ProbeSetupInterfaceSingleton,
    JointTrajectoryErrorContextInterfaceSingleton,
    MachineMaxvelInterfaceSingleton,
    LidarServiceHandler,
)
from ..interfaces.moveit_interface import PlanningErrorDetails
from ..rpl.units import force_units, ureg

from ..interfaces.feedhold_interface import FeedholdInterfaceSingleton
from ..interfaces.move_type_interface import MoveTypeInterfaceSingleton


class MoveCommand:
    name = 'move'

    PROBE_MODE_MAX_VELOCITY_SCALE = 0.1

    error_context_exception_map = {
        ECResp.PATH_TOLERANCE_VIOLATED: PathToleranceError,
        ECResp.GOAL_TOLERANCE_VIOLATED: GoalToleranceError,
        ECResp.PROBE_UNEXPECTED_RISING_EDGE: ProbeUnexpectedContactError,
        ECResp.PROBE_UNEXPECTED_FALLING_EDGE: ProbeUnexpectedContactError,
        ECResp.PROBE_CONTACT_AT_START: ProbeContactAtStartError,
        ECResp.PROBE_REACHED_MOTION_END: ProbeFailedError,
        ECResp.HARDWARE_STOP_EVENT: ProgramPause,
        ECResp.HARDWARE_ESTOP_EVENT: ProgramPause,
    }

    def __init__(self):
        self._config = ConfigInterfaceSingleton()
        self._moveit = MoveItInterfaceSingleton()
        self._joints_to_pose = JointsToPoseInterfaceSingleton()
        self._user_frames = UserFrameInterfaceSingleton()
        self._tool_frames = ToolFrameInterfaceSingleton()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()
        self._probe = ProbeSetupInterfaceSingleton()
        self._error_context = JointTrajectoryErrorContextInterfaceSingleton()
        self._maxvel = MachineMaxvelInterfaceSingleton()
        self._final_velocity_scale = 0.0
        self._final_accel_scale = 0.0
        self._probe_mode = 0
        self._move_result = None
        self.strict_limits = False
        self._feedhold_interface = FeedholdInterfaceSingleton()
        self._move_type_interface = MoveTypeInterfaceSingleton()
        self._lidar_service_handler = LidarServiceHandler()

        self._error_context_param = (
            f'{self._config.MACHINE_STATE_PREFIX}/controller_error_code'
        )

    def _handle_move_error_context(self):
        error_code = self._error_context.get_error_context()
        exc_type = self.error_context_exception_map.get(
            error_code, MoveExecutionError
        )
        message = self._error_context.get_error_message(error_code)
        raise exc_type(message)

    def _handle_planning_error_context(
        self, error_details: PlanningErrorDetails, planning_time: float
    ):
        message = f"Planning move failed after {planning_time:.3f}s: {error_details.error_message}"
        if error_details.context_error_string:
            message += f"\n{error_details.context_error_string}"
            # TODO use error_details.context_error_code to get more detailed error message
        raise MovePlanningError(message)

    def _check_target(self, target):
        if isinstance(target, (Pose, Joints, str)):
            return target
        elif isinstance(target, list):
            return Pose(*target)
        else:
            raise TypeError(
                f'{self.name} requires Pose or Joints type as target argument'
            )

    def _check_vel_accel_params(
        self,
        velocity_scale=0.5,
        accel_scale=0.5,
        accel_abs=None,
        velocity_abs=None,
        duration=None,
    ):
        if accel_scale is not None:
            if not isinstance(accel_scale, (float, int)):
                raise TypeError(
                    f"{self.name} requires a numeric values as \"accel_scale\" argument."
                )
            elif not 0.0 < accel_scale <= 1.0:
                raise ValueError(
                    f'{self.name} \"accel_scale\" parameter must be > 0.0 and <= 1.0'
                )

        if velocity_scale is not None:
            if not isinstance(velocity_scale, (float, int)):
                raise TypeError(
                    f"{self.name} requires a numeric values as \"velocity_scale\" argument."
                )
            elif not 0.0 < velocity_scale <= 1.0:
                raise ValueError(
                    f'{self.name} \"velocity_scale\" parameter must be > 0.0 and <= 1.0'
                )

        if velocity_abs is not None:
            if not isinstance(velocity_abs, (float, int, ureg.Quantity)):
                raise TypeError(
                    f"{self.name} requires a numeric value as \"velocity\" argument."
                )
            if isinstance(velocity_abs, ureg.Quantity) and velocity_abs.check(
                '1/[time]'
            ):
                velocity_scale = (
                    velocity_abs.to(ureg.radians / ureg.s).magnitude
                    / self._maxvel.cartesian_max_rot_velocity
                )
            else:
                velocity_scale = (
                    force_units(
                        velocity_abs,
                        ureg.Quantity(self._config.linear_unit)
                        / ureg.Quantity(self._config.time_unit),
                    )
                    .to(ureg.m / ureg.s)
                    .magnitude
                    / self._maxvel.cartesian_max_trans_velocity
                )

            if velocity_scale <= 0.0:
                raise ValueError("The move velocity must be greater than zero.")
            elif velocity_scale > 1.0:
                velocity_scale = 1.0
                rospy.logwarn(
                    "The specified move velocity exceeded the maximum Cartesian"
                    " velocity limit and has been clamped."
                )

        if accel_abs is not None:
            if not (isinstance(accel_abs, (float, int, ureg.Quantity))):
                raise TypeError(
                    f"{self.name} requires a numeric value as \"accel\" argument."
                )
            accel_scale = (
                force_units(
                    accel_abs,
                    ureg.Quantity(self._config.linear_unit)
                    / ureg.Quantity(self._config.time_unit) ** 2,
                )
                .to(ureg.m / ureg.s**2)
                .magnitude
            ) / self._maxvel.cartesian_max_trans_acceleration
            if accel_scale <= 0.0:
                raise ValueError(
                    "The move acceleration must be greater than zero."
                )
            elif accel_scale > 1.0:
                accel_scale = 1.0
                rospy.logwarn(
                    "The specified move acceleration exceeded the maximum"
                    " Cartesian acceleration limit and has been clamped."
                )

        if duration is not None:
            if not isinstance(duration, (float, int, ureg.Quantity)):
                raise TypeError(
                    f"{self.name} requires a numeric value as duration argument."
                )
            duration = (
                force_units(duration, ureg.Quantity(self._config.time_unit))
                .to(ureg.s)
                .magnitude
            )
            if duration <= 0.0:
                raise ValueError(
                    "The target move duration must be greater than zero."
                )
        else:
            duration = 0.0

        return velocity_scale, accel_scale, duration

    def _check_other_params(self, strict_limits):
        if not isinstance(strict_limits, bool):
            raise TypeError(
                f"{self.name} strict_limits argument must be True or False."
            )

    def _resolve_waypoint(self, target) -> Union[Pose, Joints]:
        if isinstance(target, str):
            return self._global_waypoints.get_global_waypoint(target)
        else:
            return target

    def _target_is_current(self, target):
        if isinstance(target, Pose):
            current_pose = self._joints_to_pose.get_current_pose()
            target_is_current = self._moveit.compare_poses(
                target.to_ros_pose(),
                current_pose.pose,
                position_tolerance=self._moveit.goal_position_tolerance,
                orientation_tolerance=self._moveit.goal_joint_tolerance,
            )
            # NOTE: a target pose with joint config requires additional checks
        else:
            current_joints = self._joints_to_pose.get_current_joint_values()
            target_is_current = self._moveit.compare_joints(
                target,
                current_joints,
                tolerance=self._moveit.goal_joint_tolerance,
            )

        if not target_is_current:
            return False
        rospy.logdebug("Already at target, skipping move.")
        return True

    def _check_pose_frame(self, target):
        if not target.frame:
            return
        active_frame = self._user_frames.active_frame
        if target.frame != active_frame:
            rospy.logwarn(
                f"Target pose was captured with user frame \"{target.frame}\""
                f", but a different frame is currently active."
            )

    def _apply_frames_to_pose(self, target: Pose) -> Pose:
        new_target = target
        if active_frame := self._user_frames.active_frame:
            if transform := self._user_frames.get_transform(active_frame):
                new_target = Pose.from_kdl_frame(
                    transform_to_kdl(transform) * new_target.to_kdl_frame()
                )

        if active_frame := self._tool_frames.active_frame:
            if transform := self._tool_frames.get_transform(
                active_frame, inverse=True
            ):
                new_target = Pose.from_kdl_frame(
                    new_target.to_kdl_frame() * transform_to_kdl(transform)
                )

        new_target.conf = target.conf
        new_target.rev = target.rev
        return new_target

    def _update_vel_accel(self, accel_scale, velocity_scale, use_feedrate=True):
        if self._probe_mode in (2, 3, 4, 5):
            # Force a slow maximum speed to avoid over-travel
            velocity_scale = min(
                velocity_scale, self.PROBE_MODE_MAX_VELOCITY_SCALE
            )
            rospy.loginfo(
                f"Probing: using limited velocity_scale={velocity_scale}, "
                f"accel_scale={accel_scale}"
            )
        while InterpreterProcess.spin_command():
            if use_feedrate:
                feedrate = self._maxvel.feedrate
                accel = feedrate * accel_scale
                velocity = feedrate * velocity_scale
            else:
                accel = accel_scale
                velocity = velocity_scale

            self._final_accel_scale = accel
            self._final_velocity_scale = velocity

            if (
                self._final_accel_scale > 0.0
                and self._final_velocity_scale > 0.0
            ):
                break
            else:
                rospy.sleep(SYNC_TIME)

        self._moveit.max_acceleration_scaling_factor = self._final_accel_scale
        self._moveit.max_velocity_scaling_factor = self._final_velocity_scale

    def _pause_on_soft_stop(self):
        ec = self._config.get_machine_param(self._error_context_param)
        if ec == ECResp.HARDWARE_STOP_EVENT:
            raise ProgramPause('Hardware soft stop event')

    def _execute_and_wait(self, plan):
        was_paused = False
        if self._probe_mode:
            # Probe mode only lasts for the next planned move,
            # so we only need to set it if it's not a default
            self._probe.set_next_probe_move(self._probe_mode)
        self._moveit.execute(plan, wait=False)  # then execute
        try:
            while InterpreterProcess.spin_pause():
                if was_paused:
                    self._lidar_service_handler.resume_data_collection()
                    self._feedhold_interface.toggle_feedhold(False)
                    rospy.loginfo('Continuing executing move')
                    was_paused = False

                try:
                    while InterpreterProcess.spin_command():
                        if not self._moveit.execution_active:
                            self._pause_on_soft_stop()
                            message = (
                                f'Executing move {self._moveit.execution_status_text}: '
                                f'{self._moveit.execution_message}'
                            )

                            rospy.loginfo(message)
                            if not self._moveit.success:
                                self._handle_move_error_context()
                            break
                        rospy.sleep(SYNC_TIME)

                    # Only query for probe result if the move completed successfully
                    if (
                        self._probe_mode in (2, 3, 4, 5)
                        and self._moveit.success
                    ):
                        self._move_result = self._probe.get_probe_result()
                    break

                except ProgramPause as e:
                    self._lidar_service_handler.pause_data_collection()
                    self._feedhold_interface.toggle_feedhold(True)
                    rospy.loginfo(f'Paused executing move:  {e}')
                    was_paused = True

        except ProgramExit as e:
            self._lidar_service_handler.clear_data_collection()
            if was_paused:
                self._moveit.stop()
                self._moveit._set_execution_active(False)
                rospy.sleep(0.5)
                self._feedhold_interface.toggle_feedhold(False)

            else:
                self._moveit.stop()
                self._moveit._set_execution_active(False)
                while self._moveit.execution_active:
                    rospy.sleep(SYNC_TIME)

            while self._moveit.execution_active:
                rospy.sleep(SYNC_TIME)
            raise e

    def _plan_and_wait(self, target, planner, **kwargs):
        self._move_type_interface.specify_program_move(
            self._final_velocity_scale
        )

        if planner['pipeline_id'] == self._moveit.PILZ_PLANNER_PIPELINE:
            self._moveit.set_pilz_industrial_motion_planner_parameters(
                strict_limits=self.strict_limits
            )
        self._moveit.plan(
            target,
            wait=False,
            **planner,
            **kwargs,
        )
        try:
            while (
                InterpreterProcess.spin_command()
                and self._moveit.planning_active
            ):
                rospy.sleep(SYNC_TIME)
        except (ProgramExit, ProgramPause) as e:
            if isinstance(e, ProgramPause):
                rospy.loginfo(f'Paused planning move:  {e}')
            self._moveit.stop()
            while self._moveit.planning_active:
                rospy.sleep(SYNC_TIME)
            raise e
        (
            success,
            plan,
            planning_time,
            error_details,
        ) = self._moveit.planning_result

        if success:
            rospy.loginfo(
                f"Planning move successful, time: {planning_time:.3f}s"
            )
        else:
            self._handle_planning_error_context(error_details, planning_time)

        return plan

    def _plan_sequence(self, sequence):
        self._moveit.set_pilz_industrial_motion_planner_parameters(
            strict_limits=self.strict_limits
        )
        (
            success,
            plan,
            planning_time,
            error_details,
        ) = self._moveit.plan_sequence(sequence)

        if success:
            rospy.loginfo(
                f"Planning sequence successful, time: {planning_time:.3f}s"
            )
        else:
            self._handle_planning_error_context(error_details, planning_time)

        return plan

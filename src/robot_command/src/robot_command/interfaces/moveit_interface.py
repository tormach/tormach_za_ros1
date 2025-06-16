import threading
import time
from typing import Tuple, Union, List

import actionlib
import rospy
from actionlib_msgs.msg import GoalStatus
from control_msgs.msg import JointTrajectoryControllerState
from moveit_msgs.msg import (
    MoveGroupAction,
    ExecuteTrajectoryAction,
    MoveGroupGoal,
    Constraints,
    PositionConstraint,
    BoundingVolume,
    OrientationConstraint,
    JointConstraint,
    MoveGroupFeedback,
    MoveGroupResult,
    ExecuteTrajectoryFeedback,
    ExecuteTrajectoryResult,
    ExecuteTrajectoryGoal,
    MoveItErrorCodes,
    RobotTrajectory,
    MotionPlanRequest,
    MoveGroupSequenceGoal,
    MotionSequenceItem,
    MoveGroupSequenceAction,
    MoveGroupSequenceFeedback,
    MoveGroupSequenceResult,
)
from moveit_msgs.srv import (
    RetimeTrajectory,
    RetimeTrajectoryRequest,
    GetPlanningErrorDetails,
    GetPlanningErrorDetailsRequest,
)
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose as RosPose
from trajectory_msgs.msg import JointTrajectoryPoint

from ..rpl import Pose
from movej_ik_server.movej_ik_server_handler import (
    MovejIkServerHandler,
    inverted_robot_configs,
)


_signal_chain = {}


class PositionControllerState:
    STATE_TOPIC = 'position_trajectory_controller/state'

    def __init__(self):
        self._last_time_from_start = rospy.Duration()
        self._current_time_from_start = rospy.Duration()
        self._positions = []

        self._sub = rospy.Subscriber(
            self.STATE_TOPIC,
            JointTrajectoryControllerState,
            self._on_state_msg_received,
        )

    @property
    def last_time_from_start(self):
        return self._last_time_from_start

    @property
    def current_time_from_start(self):
        return self._current_time_from_start

    @property
    def current_positions(self):
        return self._positions

    def stop(self):
        self._sub.unregister()

    def _on_state_msg_received(self, msg: JointTrajectoryControllerState):
        last_time_from_start = msg.desired.time_from_start
        if not last_time_from_start.is_zero():
            self._last_time_from_start = last_time_from_start
            self._current_time_from_start = msg.actual.time_from_start
            self._positions = msg.actual.positions


class PilzPlanningErrorDetails:
    GET_PLANNING_ERROR_DETAILS_SERVICE = (
        '/move_group/pilz_industrial_motion_planner/get_planning_error_details'
    )

    def __init__(self):
        self._error_code = 0
        self._error_message = ''
        self._get_error_details_srv = rospy.ServiceProxy(
            self.GET_PLANNING_ERROR_DETAILS_SERVICE, GetPlanningErrorDetails
        )
        self._get_error_details_srv.wait_for_service()

    @property
    def error_code(self):
        return self._error_code

    @property
    def error_message(self):
        return self._error_message

    def update(self):
        res = self._get_error_details_srv(GetPlanningErrorDetailsRequest())
        self._error_code = res.error_code.val
        self._error_message = res.message


class PlanningErrorDetails:
    __slots__ = (
        'error_code',
        'error_message',
        'context_error_string',
        'context_error_code',
    )

    ERROR_CODE_TO_MESSAGE = {
        MoveItErrorCodes.INVALID_MOTION_PLAN: "Invalid motion plan",
        MoveItErrorCodes.MOTION_PLAN_INVALIDATED_BY_ENVIRONMENT_CHANGE: "Motion plan invalidated by environment change",
        MoveItErrorCodes.CONTROL_FAILED: "Control failed",
        MoveItErrorCodes.UNABLE_TO_AQUIRE_SENSOR_DATA: "Unable to acquire sensor data",
        MoveItErrorCodes.TIMED_OUT: "Timed out",
        MoveItErrorCodes.PREEMPTED: "Preempted",
        MoveItErrorCodes.START_STATE_IN_COLLISION: "Start state in collision",
        MoveItErrorCodes.START_STATE_VIOLATES_PATH_CONSTRAINTS: "Start state violates path constraints",
        MoveItErrorCodes.GOAL_IN_COLLISION: "Goal in collision",
        MoveItErrorCodes.GOAL_VIOLATES_PATH_CONSTRAINTS: "Goal violates path constraints",
        MoveItErrorCodes.GOAL_CONSTRAINTS_VIOLATED: "Goal constraints violated",
        MoveItErrorCodes.INVALID_GROUP_NAME: "Invalid group name",
        MoveItErrorCodes.INVALID_GOAL_CONSTRAINTS: "Invalid goal constraints",
        MoveItErrorCodes.INVALID_ROBOT_STATE: "Invalid robot state",
        MoveItErrorCodes.INVALID_LINK_NAME: "Invalid link name",
        MoveItErrorCodes.INVALID_OBJECT_NAME: "Invalid object name",
        MoveItErrorCodes.FRAME_TRANSFORM_FAILURE: "Frame transform failure",
        MoveItErrorCodes.COLLISION_CHECKING_UNAVAILABLE: "Collision checking unavailable",
        MoveItErrorCodes.ROBOT_STATE_STALE: "Robot state stale",
        MoveItErrorCodes.SENSOR_INFO_STALE: "Sensor info stale",
        MoveItErrorCodes.COMMUNICATION_FAILURE: "Communication failure",
        MoveItErrorCodes.NO_IK_SOLUTION: "No IK solution",
    }

    def __init__(
        self,
        error_code: int,
        context_error_string: str,
        context_error_code: int,
    ):
        self.error_code = error_code
        self.error_message = self.ERROR_CODE_TO_MESSAGE.get(
            error_code, "Unknown error"
        )
        self.context_error_string = context_error_string
        self.context_error_code = context_error_code


class PilzPlanningParameters:
    PILZ_PLANNING_PARAMETERS_NAMESPACE = (
        "/move_group/pilz_industrial_motion_planner/planning_parameters"
    )

    def _get_param(self, param_name):
        return rospy.get_param(
            f"{self.PILZ_PLANNING_PARAMETERS_NAMESPACE}/{param_name}"
        )

    def _set_param(self, param_name, value):
        rospy.set_param(
            f"{self.PILZ_PLANNING_PARAMETERS_NAMESPACE}/{param_name}", value
        )

    @property
    def sampling_time_s(self):
        return self._get_param("sampling_time")

    @sampling_time_s.setter
    def sampling_time_s(self, value):
        self._set_param("sampling_time", value)

    @property
    def sampling_distance_m(self):
        return self._get_param("sampling_distance")

    @sampling_distance_m.setter
    def sampling_distance_m(self, value):
        self._set_param("sampling_distance", value)

    @property
    def output_tcp_joints(self):
        return self._get_param("output_tcp_joints")

    @output_tcp_joints.setter
    def output_tcp_joints(self, value):
        self._set_param("output_tcp_joints", value)

    @property
    def trim_on_failure(self):
        return self._get_param("trim_on_failure")

    @trim_on_failure.setter
    def trim_on_failure(self, value):
        self._set_param("trim_on_failure", value)

    @property
    def strict_limits(self):
        return self._get_param("strict_limits")

    @strict_limits.setter
    def strict_limits(self, value):
        self._set_param("strict_limits", value)

    @property
    def min_scaling_correction_factor(self):
        return self._get_param("min_scaling_correction_factor")

    @min_scaling_correction_factor.setter
    def min_scaling_correction_factor(self, value):
        self._set_param("min_scaling_correction_factor", value)


class MoveItInterface:
    DEFAULT_WAIT_TIMEOUT_S = 10.0
    MOVE_GROUP_ACTION = 'move_group'
    SEQUENCE_MOVE_GROUP_ACTION = 'sequence_move_group'
    EXECUTE_TRAJECTORY_ACTION = 'execute_trajectory'
    RETIME_TRAJECTORY_SERVICE = 'retime_trajectory'
    # default settings for pilz planner
    DEFAULT_DYNAMIC_SAMPLING_TIME_S = 0.01
    DEFAULT_CONST_SAMPLING_DISTANCE_M = 0.005
    DEFAULT_MIN_SCALING_CORRECTION_FACTOR = 0.01

    PILZ_PLANNER_PIPELINE = 'pilz_industrial_motion_planner'
    LIN_MOVE_PLANNER = {
        'pipeline_id': PILZ_PLANNER_PIPELINE,
        'planner_id': 'LIN',
    }
    PTP_MOVE_PLANNER = {
        'pipeline_id': PILZ_PLANNER_PIPELINE,
        'planner_id': 'PTP',
    }
    CIRC_MOVE_PLANNER = {
        'pipeline_id': PILZ_PLANNER_PIPELINE,
        'planner_id': 'CIRC',
    }
    FREE_MOVE_PLANNER = {
        'pipeline_id': 'ompl',
        'planner_id': '',
    }

    _feedback_status_map = {
        getattr(GoalStatus, a): a
        for a in dir(GoalStatus)
        if 65 <= ord(a[0]) <= 90
    }

    def __init__(self):
        self._planning_active = False
        self._planning_active_lock = threading.Lock()
        self._planning_status = None
        self._planning_message = ""
        self._planning_result = None
        self._planning_goal = None
        self._execution_active = False
        self._execution_active_lock = threading.Lock()
        self._execution_status = None
        self._execution_message = ""
        self._execution_result = None
        self._execution_goal = None
        self._success = False

        self.execution_active_changed = []
        self.planning_active_changed = []

        # load params
        self.group_name = rospy.get_param('moveit/move_group', None)
        if self.group_name is None:
            raise RuntimeError("ROS param 'moveit/move_group' unset")
        self.joint_names = rospy.get_param('/moveit/joint_names', None)
        if self.joint_names is None:
            raise RuntimeError("ROS param 'moveit/joint_names' unset")
        self.allow_replanning = rospy.get_param('moveit/allow_replanning', True)
        self.pose_reference_frame = rospy.get_param(
            'moveit/pose_reference_frame', None
        )
        if self.pose_reference_frame is None:
            raise RuntimeError("ROS param 'moveit/pose_reference_frame' unset")
        self.tool_reference_frame = rospy.get_param(
            'moveit/tool_reference_frame', None
        )
        if self.tool_reference_frame is None:
            raise RuntimeError("ROS param 'moveit/tool_reference_frame' unset")
        self.goal_position_tolerance = rospy.get_param(
            'moveit/goal_position_tolerance', 0.001
        )
        self.goal_orientation_tolerance = rospy.get_param(
            'moveit/goal_orientation_tolerance', 0.01
        )
        self.goal_joint_tolerance = rospy.get_param(
            'moveit/goal_joint_tolerance', 0.001
        )
        self.goal_joint_correction_tolerance = rospy.get_param(
            'moveit/goal_joint_correction_tolerance', self.goal_joint_tolerance
        )
        self.planning_time = rospy.get_param('moveit/planning_time', 0.5)
        self.num_planning_attempts = rospy.get_param(
            'moveit/num_planning_attempts', 1
        )
        self.planner_id = rospy.get_param('moveit/planner_id', '')
        self.retime_algorithm = rospy.get_param(
            'moveit/retime_algorithm', 'time_optimal_trajectory_generation'
        )

        self.max_velocity_scaling_factor = 1.0
        self.max_acceleration_scaling_factor = 1.0
        self.blend_radius = 0.0

        self._controller_state = PositionControllerState()

        self._move_group_action = actionlib.SimpleActionClient(
            self.MOVE_GROUP_ACTION, MoveGroupAction
        )
        self._seq_move_group_action = actionlib.SimpleActionClient(
            self.SEQUENCE_MOVE_GROUP_ACTION, MoveGroupSequenceAction
        )
        self._execute_trajectory_action = actionlib.SimpleActionClient(
            self.EXECUTE_TRAJECTORY_ACTION, ExecuteTrajectoryAction
        )
        self._retime_trajectory_srv = rospy.ServiceProxy(
            self.RETIME_TRAJECTORY_SERVICE, RetimeTrajectory
        )
        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._move_group_action.wait_for_server(
            rospy.Duration.from_sec(wait_timeout_s)
        )
        self._seq_move_group_action.wait_for_server(
            rospy.Duration.from_sec(wait_timeout_s)
        )
        self._execute_trajectory_action.wait_for_server(
            rospy.Duration.from_sec(wait_timeout_s)
        )
        self._retime_trajectory_srv.wait_for_service(wait_timeout_s)

        self._planner_error_details = PilzPlanningErrorDetails()
        self._pilz_planning_params = PilzPlanningParameters()
        self._movej_handler = MovejIkServerHandler()
        self._requested_config = None

    @property
    def planning_active(self):
        with self._planning_active_lock:
            return self._planning_active

    @property
    def planning_status(self):
        return self._planning_status

    @property
    def planning_status_text(self):
        return self._feedback_status_map[self._planning_status]

    @property
    def planning_message(self):
        return self._planning_message

    @property
    def planning_result(
        self,
    ) -> Tuple[bool, RobotTrajectory, float, PlanningErrorDetails]:
        """
        Returns the result of the last planning request.

        :return: Tuple of success, trajectory, planning time, error details
        """
        return self._planning_result

    @property
    def execution_active(self):
        with self._execution_active_lock:
            return self._execution_active

    @property
    def execution_status(self):
        return self._execution_status

    @property
    def execution_status_text(self):
        return self._feedback_status_map[self._execution_status]

    @property
    def execution_message(self):
        return self._execution_message

    @property
    def execution_result(self):
        return self._execution_result

    @property
    def success(self):
        return self._success

    def plan(
        self,
        target: Union[RosPose, Pose, List[float]],
        wait: bool = True,
        interim_target: Union[RosPose, Pose] = None,
        **kwargs,
    ):
        goal = MoveGroupGoal()

        # 1. - 9. create planning request
        goal.request = self._create_request(target, interim_target, **kwargs)

        # 10. - 12. fill planning request
        self._fill_planning_options(goal)

        # 13. send goal
        self._set_planning_active(True)
        self._planning_goal = goal
        self._move_group_action.stop_tracking_goal()
        self._move_group_action.send_goal(
            goal,
            active_cb=self._move_group_active_cb,
            feedback_cb=self._move_group_feedback_cb,
            done_cb=self._move_group_done_cb,
        )
        if not wait:
            return None
        while (
            self._move_group_action.wait_for_result() and self.planning_active
        ):
            pass  # wait to prevent race condition in actionlib
        return self._planning_result

    def create_sequence_item(
        self,
        target: Union[RosPose, Pose, List[float]],
        interim_target: Union[RosPose, Pose] = None,
        **kwargs,
    ):
        return self._create_request(target, interim_target, **kwargs)

    def plan_sequence(
        self, sequence: List[MotionPlanRequest], wait: bool = True
    ):
        goal = MoveGroupSequenceGoal()

        for i, request in enumerate(sequence):
            # Create and fill request
            sequence_item = MotionSequenceItem()
            sequence_item.blend_radius = (
                0.0 if i == (len(sequence) - 1) else self.blend_radius
            )
            sequence_item.req = request

            # Add request to goal
            goal.request.items.append(sequence_item)

        self._fill_planning_options(goal)

        # 13. send goal
        self._set_planning_active(True)
        self._planning_goal = goal
        self._seq_move_group_action.stop_tracking_goal()
        self._seq_move_group_action.send_goal(
            goal,
            active_cb=self._seq_move_group_active_cb,
            feedback_cb=self._seq_move_group_feedback_cb,
            done_cb=self._seq_move_group_done_cb,
        )
        if not wait:
            return None
        while (
            self._seq_move_group_action.wait_for_result()
            and self.planning_active
        ):
            pass  # wait to prevent race condition in actionlib
        return self._planning_result

    def execute(self, plan: RobotTrajectory, wait: bool = True):
        g = ExecuteTrajectoryGoal()

        g.trajectory = plan

        self._set_execution_active(True)
        self._execute_trajectory_action.stop_tracking_goal()
        self._execute_trajectory_action.send_goal(
            g,
            active_cb=self._execute_trajectory_active_cb,
            feedback_cb=self._execute_trajectory_feedback_cb,
            done_cb=self._execute_trajectory_done_cb,
        )
        if not wait:
            return None
        while (
            self._execute_trajectory_action.wait_for_result()
            and self._execution_active
        ):
            pass  # wait to prevent race condition in actionlib
        return self._execution_result

    def stop(self):
        self._move_group_action.cancel_all_goals()
        self._execute_trajectory_action.cancel_all_goals()

    def shutdown(self):
        self._move_group_action.cancel_all_goals()
        self._execute_trajectory_action.cancel_all_goals()
        self._controller_state.stop()

    def recompute_trajectory(
        self,
        trajectory: RobotTrajectory,
        acceleration_scaling_factor,
        velocity_scaling_factor,
        algorithm=None,
    ):
        if not algorithm:
            algorithm = self.retime_algorithm
        time_from_start = self._controller_state.current_time_from_start
        index = next(
            i
            for i, point in enumerate(trajectory.joint_trajectory.points)
            if point.time_from_start > time_from_start
        )

        start_point = JointTrajectoryPoint()
        start_point.time_from_start = (
            self._controller_state.current_time_from_start
        )
        start_point.positions = self._controller_state.current_positions
        start_point.velocities = [0.0] * len(start_point.positions)
        start_point.accelerations = [0.0] * len(start_point.positions)
        trajectory.joint_trajectory.points = [
            start_point
        ] + trajectory.joint_trajectory.points[index:]

        plan = self.retime_trajectory(
            trajectory,
            velocity_scaling_factor=velocity_scaling_factor,
            acceleration_scaling_factor=acceleration_scaling_factor,
            algorithm=algorithm,
        )
        if plan:
            self._fix_plan_time_from_start(plan)
        return plan

    @staticmethod
    def compare_poses(
        pose1: RosPose,
        pose2: RosPose,
        position_tolerance: float,
        orientation_tolerance: float,
    ):
        p1 = pose1.position
        p2 = pose2.position
        position_match = (
            abs(p1.x - p2.x) <= position_tolerance
            and abs(p1.y - p2.y) <= position_tolerance
            and abs(p1.z - p2.z) <= position_tolerance
        )
        o1 = pose1.orientation
        o2 = pose2.orientation
        # q = -q for orientations
        orientation_match = (
            abs(o1.x - o2.x) <= orientation_tolerance
            and abs(o1.y - o2.y) <= orientation_tolerance
            and abs(o1.z - o2.z) <= orientation_tolerance
            and abs(o1.w - o2.w) <= orientation_tolerance
        ) or (
            abs(o1.x + o2.x) <= orientation_tolerance
            and abs(o1.y + o2.y) <= orientation_tolerance
            and abs(o1.z + o2.z) <= orientation_tolerance
            and abs(o1.w + o2.w) <= orientation_tolerance
        )
        return position_match and orientation_match

    @staticmethod
    def compare_joints(
        joints1: List[float], joints2: List[float], tolerance: float
    ):
        matched = True
        for i in range(len(joints1)):
            matched &= abs(joints1[i] - joints2[i]) <= tolerance
        return matched

    # def movej_ik_get_config(self, target, arm_config, rev_count=0):
    # try:
    # response = self.movej_closest_ik_service_client()
    # return response.arm_config, True
    # except rospy.ServiceException as e:
    # rospy.logerr("Service call failed: %s" % e)
    # return None, False

    def _create_request(self, target, interim_target, **kwargs):
        request = MotionPlanRequest()
        # 1. fill in request workspace_parameters
        # 2. fill in request start_state
        try:
            request.start_state = kwargs["start_state"]
        except KeyError:
            request.start_state.is_diff = True

        if isinstance(target, Pose):
            self._requested_config = target.conf
        else:
            self._requested_config = None

        # quick fix
        if isinstance(target, list) and all(
            isinstance(item, float) for item in target
        ):
            # rospy.logerr("called move command with list of floats, assuming joints")
            self._move_type = "joints"
        else:
            self._move_type = "pose"

        # 3. fill in request goal_constraints
        if (
            isinstance(target, Pose)
            and kwargs["planner_id"] == self.PTP_MOVE_PLANNER['planner_id']
        ):
            # rospy.logwarn("movej_user_ik_service_call() returned: %s" % target)

            (
                my_target_joints,
                success,
            ) = self._movej_handler.call_movej_ik_server(target)

            if success:
                self._create_request_joint_goal_constraint(
                    my_target_joints, request
                )
            else:
                raise ValueError(
                    "Failed to find IK solution for movej() with p[] target"
                )

        elif isinstance(target, (RosPose, Pose)):
            if isinstance(target, Pose):
                target = target.to_ros_pose()
            self._create_request_pose_goal_constraint(target, request)

        elif isinstance(target, list):
            self._create_request_joint_goal_constraint(target, request)
        else:
            rospy.logerr("Unknown target type")
            return None

        # 4. fill in request path constraints
        if interim_target:
            if isinstance(interim_target, Pose):
                interim_target = interim_target.to_ros_pose()
            self._create_request_interim_target_path_constraint(
                interim_target, request
            )

        # 5. fill in request trajectory constraints

        # 6. fill in request pipeline and planner id
        try:
            request.pipeline_id = kwargs["pipeline_id"]
        except KeyError:
            request.pipeline_id = 'ompl'
        try:
            request.planner_id = kwargs["planner_id"]
        except KeyError:
            if self.planner_id:
                request.planner_id = self.planner_id

        # 7. fill in request group name
        request.group_name = self.group_name

        # 8. fill in request number of planning attempts
        try:
            request.num_planning_attempts = kwargs["num_attempts"]
        except KeyError:
            request.num_planning_attempts = self.num_planning_attempts

        # 9. fill in request allowed planning time
        try:
            request.allowed_planning_time = kwargs["planning_time"]
        except KeyError:
            request.allowed_planning_time = self.planning_time

        # 10. Fill in velocity/acceleration scaling factor
        try:
            request.max_velocity_scaling_factor = kwargs[
                "max_velocity_scaling_factor"
            ]
        except KeyError:
            fac = self.max_velocity_scaling_factor
            request.max_velocity_scaling_factor = fac
        try:
            request.max_acceleration_scaling_factor = kwargs[
                "max_acceleration_scaling_factor"
            ]
        except KeyError:
            fac = self.max_acceleration_scaling_factor
            request.max_acceleration_scaling_factor = fac

        # 11. fill in target duration
        try:
            request.duration = kwargs["duration"]
        except KeyError:
            request.duration = 0.0

        return request

    def _create_request_interim_target_path_constraint(
        self, interim_target, request
    ):
        pose = interim_target
        c = Constraints()
        c.name = "interim"
        c.position_constraints.append(PositionConstraint())
        c.position_constraints[0].header.frame_id = self.pose_reference_frame
        c.position_constraints[0].link_name = self.tool_reference_frame
        bounding_volume = BoundingVolume()
        primitive = SolidPrimitive()
        primitive.dimensions = [float('+inf')]
        primitive.type = primitive.SPHERE
        bounding_volume.primitives.append(primitive)
        interim_pose = RosPose()
        interim_pose.position = pose.position
        bounding_volume.primitive_poses.append(pose)
        c.position_constraints[0].constraint_region = bounding_volume
        c.position_constraints[0].weight = 1.0
        request.path_constraints = c

    def _create_request_joint_goal_constraint(self, target, request):
        joints = target
        constraints = Constraints()
        for i in range(len(joints)):
            constraints.joint_constraints.append(
                JointConstraint(
                    joint_name=self.joint_names[i],
                    position=joints[i],
                    tolerance_above=self.goal_joint_tolerance,
                    tolerance_below=self.goal_joint_tolerance,
                    weight=1.0,
                )
            )
        request.goal_constraints.append(constraints)

    def _create_request_pose_goal_constraint(self, target, request):
        pose = target
        c = Constraints()
        c.position_constraints.append(PositionConstraint())
        c.position_constraints[0].header.frame_id = self.pose_reference_frame
        c.position_constraints[0].link_name = self.tool_reference_frame
        bounding_volume = BoundingVolume()
        solid_primitive = SolidPrimitive()
        solid_primitive.dimensions = [self.goal_position_tolerance]
        solid_primitive.type = solid_primitive.SPHERE
        bounding_volume.primitives.append(solid_primitive)
        bounding_volume.primitive_poses.append(pose)
        c.position_constraints[0].constraint_region = bounding_volume
        c.position_constraints[0].weight = 1.0
        c.orientation_constraints.append(OrientationConstraint())
        c.orientation_constraints[0].header.frame_id = self.pose_reference_frame
        c.orientation_constraints[0].orientation = pose.orientation
        c.orientation_constraints[0].link_name = self.tool_reference_frame
        tolerance = self.goal_orientation_tolerance
        c.orientation_constraints[0].absolute_x_axis_tolerance = tolerance
        c.orientation_constraints[0].absolute_y_axis_tolerance = tolerance
        c.orientation_constraints[0].absolute_z_axis_tolerance = tolerance
        c.orientation_constraints[0].weight = 1.0
        request.goal_constraints.append(c)

    def _fill_planning_options(self, goal):
        # 10. fill in planning options diff
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True

        # 11. fill in planning options plan only
        goal.planning_options.plan_only = True

        # 12. fill in other planning options
        goal.planning_options.look_around = False
        goal.planning_options.replan = self.allow_replanning

    @staticmethod
    def _fix_plan_time_from_start(plan: RobotTrajectory):
        plan.joint_trajectory.points[0].time_from_start.nsecs += 1

    def retime_trajectory(
        self,
        trajectory: RobotTrajectory,
        velocity_scaling_factor=1.0,
        acceleration_scaling_factor=1.0,
        tcp_velocity_scaling_factor=None,
        tcp_acceleration_scaling_factor=None,
        algorithm=None,
    ):
        if not algorithm:
            algorithm = self.retime_algorithm
        req = RetimeTrajectoryRequest()
        has_tcp_values = (
            tcp_velocity_scaling_factor is not None
            or tcp_acceleration_scaling_factor is not None
        )
        req.group_name = (
            f'{self.group_name}_tcp' if has_tcp_values else self.group_name
        )
        req.acceleration_scaling_factor = acceleration_scaling_factor
        req.velocity_scaling_factor = velocity_scaling_factor
        if has_tcp_values:
            req.joint_names = ['tcp_lin', 'tcp_rot']
            req.joint_velocity_scaling_factors = [
                tcp_velocity_scaling_factor
            ] * 2
            req.joint_acceleration_scaling_factors = [
                tcp_acceleration_scaling_factor
            ] * 2
        req.trajectory = trajectory
        req.algorithm = algorithm
        result = self._retime_trajectory_srv(req)
        if result.error_code.val == MoveItErrorCodes.SUCCESS:
            return result.trajectory
        rospy.logerr(f"re-timing trajectory failed: {result.error_code}")
        return None

    def _fix_plan_endpoint(
        self, plan: RobotTrajectory, request: MotionPlanRequest
    ):
        endpoint = plan.joint_trajectory.points[-1]
        joint_constraints = request.goal_constraints[0].joint_constraints
        if len(joint_constraints) > 0:
            joints_target = [j.position for j in joint_constraints]
            endpoint_joints = endpoint.positions[
                : len(joints_target)
            ]  # remove tcp joints
            # correct trajectory endpoint with exact goal position
            # if target position approximately matches the goal pos
            correction_limit = (
                self.goal_joint_tolerance + self.goal_joint_correction_tolerance
            )
            # QE: Why we need to correct joints poses?
            if MoveItInterface.compare_joints(
                endpoint_joints,
                joints_target,
                tolerance=correction_limit,
            ):
                rospy.loginfo(
                    f"Correcting end point from {endpoint.positions} to {joints_target}"
                )
                endpoint.positions = joints_target
        endpoint.velocities = [0.0] * len(endpoint.velocities)
        endpoint.accelerations = [0.0] * len(endpoint.accelerations)

    def _set_planning_active(self, value):
        with self._planning_active_lock:
            self._planning_active = value
        for cb in self.planning_active_changed:
            rospy.Timer(
                rospy.Duration.from_sec(0.001),
                lambda _: cb(value),
                oneshot=True,
            )  # decouple from actionlib as goal state transition happens after callback

    def _set_execution_active(self, value):
        with self._execution_active_lock:
            self._execution_active = value
        for cb in self.execution_active_changed:
            rospy.Timer(
                rospy.Duration.from_sec(0.001),
                lambda _: cb(value),
                oneshot=True,
            )  # decouple from actionlib as goal state transition happens after callback

    @staticmethod
    def _move_group_active_cb():
        rospy.logdebug("Planning active")

    @staticmethod
    def _move_group_feedback_cb(feedback: MoveGroupFeedback):
        rospy.logdebug(f'Planning feedback {feedback.state}')

    @staticmethod
    def _get_goal_status_text(action):
        return action.get_goal_status_text() if action.gh else "No goal handle"

    def _move_group_done_cb(self, status: int, result: MoveGroupResult):
        self._planning_status = status
        self._planning_message = self._get_goal_status_text(
            self._move_group_action
        )

        self._success = result.error_code.val == MoveItErrorCodes.SUCCESS
        planned_trajectory = result.planned_trajectory
        planning_time = result.planning_time
        error_details = None
        if self._success:
            request = self._planning_goal.request
            start_time = time.time()
            if planned_trajectory is None:
                self._success = False
            else:
                self._fix_plan_time_from_start(planned_trajectory)
                self._fix_plan_endpoint(planned_trajectory, request)

                # quick fix: allow the user to jog as they wish
                # consider only moves other than joint goals
                if self._move_type != "joints":
                    # check if goal arm config is allowed
                    endpoint = planned_trajectory.joint_trajectory.points[-1]
                    endpoint_joints = endpoint.positions[
                        :6
                    ]  # robot joints only, exclude end-effector 'joints'

                    (
                        response,
                        _,
                    ) = self._movej_handler.get_arm_config_service_call(
                        endpoint_joints
                    )

                    # resulted config not in the allowed configs
                    cond1 = response.is_arm_config_valid is False
                    # user requested a specific config, but it is not the same as the legal goal config for a given move
                    # requested config is specifed in the Pose command
                    cond2 = (
                        self._requested_config is not None
                        and self._requested_config.value != response.arm_config
                    )
                    # use did not request a specific arm config
                    cond3 = self._requested_config is None

                    if cond2 or (cond1 and cond3):
                        config_name = inverted_robot_configs.get(
                            response.arm_config
                        )
                        rospy.logerr(
                            f"Valid goal arm config {config_name} not allowed by current constraints."
                        )
                        if cond2:
                            req_config_name = inverted_robot_configs.get(
                                self._requested_config.value
                            )
                            rospy.logerr(
                                f"Invalid arm config requested for this move: {req_config_name}"
                            )

                        error_details = PlanningErrorDetails(
                            error_code=result.error_code.val,
                            context_error_string="Goal arm config is not allowed.",
                            context_error_code=result.error_code.val,
                        )

                        self._planning_result = (
                            self._success,
                            planned_trajectory,
                            result.planning_time,
                            error_details,
                        )
                        self._set_planning_active(False)
                        self._requested_config = None
                        planning_time += time.time() - start_time
                        return

                    # clean up requested config before the next move
                    self._requested_config = None

            planning_time += time.time() - start_time
        elif (
            self._planning_goal.request.pipeline_id
            == self.PILZ_PLANNER_PIPELINE
        ):
            self._planner_error_details.update()
            error_details = PlanningErrorDetails(
                error_code=result.error_code.val,
                context_error_string=self._planner_error_details.error_message,
                context_error_code=self._planner_error_details.error_code,
            )
        else:
            error_details = PlanningErrorDetails(
                error_code=result.error_code.val,
                context_error_string="",
                context_error_code=result.error_code.val,
            )

        self._planning_result = (
            self._success,
            planned_trajectory,
            result.planning_time,
            error_details,
        )
        self._set_planning_active(False)

    @staticmethod
    def _seq_move_group_active_cb():
        rospy.logdebug("Sequence planning active")

    @staticmethod
    def _seq_move_group_feedback_cb(feedback: MoveGroupSequenceFeedback):
        rospy.logdebug(f'Sequence planning feedback {feedback.state}')

    def _seq_move_group_done_cb(
        self, status: int, result: MoveGroupSequenceResult
    ):
        response = result.response
        self._planning_status = status
        self._planning_message = self._get_goal_status_text(
            self._seq_move_group_action
        )
        self._success = response.error_code.val == MoveItErrorCodes.SUCCESS
        planned_trajectory = (
            response.planned_trajectories[0] if self._success else None
        )
        request = self._planning_goal.request.items[-1].req
        planning_time = response.planning_time
        if self._success:
            start_time = time.time()
            self._fix_plan_time_from_start(planned_trajectory)
            self._fix_plan_endpoint(planned_trajectory, request)
            planning_time += time.time() - start_time
        self._planning_result = (
            self._success,
            planned_trajectory,
            response.planning_time,
            response.error_code,
        )
        self._set_planning_active(False)

    @staticmethod
    def _execute_trajectory_active_cb():
        rospy.logdebug("Execute trajectory active")

    @staticmethod
    def _execute_trajectory_feedback_cb(feedback: ExecuteTrajectoryFeedback):
        rospy.logdebug(f'Execute trajectory feedback {feedback.state}')

    def _execute_trajectory_done_cb(
        self, status: int, result: ExecuteTrajectoryResult
    ):
        self._execution_status = status
        self._execution_message = self._get_goal_status_text(
            self._execute_trajectory_action
        )
        self._success = status == GoalStatus.SUCCEEDED
        self._execution_result = result.error_code
        self._set_execution_active(False)

    def set_pilz_industrial_motion_planner_parameters(
        self,
        sampling_time_s=None,
        sampling_distance_m=None,
        output_tcp_joints=True,
        trim_on_failure=False,
        strict_limits=False,
        min_scaling_correction_factor=None,
    ):
        if sampling_time_s is None:
            sampling_time_s = self.DEFAULT_DYNAMIC_SAMPLING_TIME_S
        if sampling_distance_m is None:
            sampling_distance_m = self.DEFAULT_CONST_SAMPLING_DISTANCE_M
        if min_scaling_correction_factor is None:
            min_scaling_correction_factor = (
                self.DEFAULT_MIN_SCALING_CORRECTION_FACTOR
            )
        self._pilz_planning_params.sampling_time_s = sampling_time_s
        self._pilz_planning_params.sampling_distance_m = sampling_distance_m
        self._pilz_planning_params.output_tcp_joints = output_tcp_joints
        self._pilz_planning_params.trim_on_failure = trim_on_failure
        self._pilz_planning_params.strict_limits = strict_limits
        self._pilz_planning_params.min_scaling_correction_factor = (
            min_scaling_correction_factor
        )


class MoveItInterfaceSingleton:
    """
    Singleton interface class to MoveIt

    Initializing MoveGroupCommander takes some time and therefore, should
    only be done once per program.
    """

    _instance = None

    def __init__(self):
        if not MoveItInterfaceSingleton._instance:
            MoveItInterfaceSingleton._instance = MoveItInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

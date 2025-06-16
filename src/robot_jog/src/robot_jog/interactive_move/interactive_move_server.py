import time
from collections import namedtuple
from copy import deepcopy
from functools import partial
from math import pi
from threading import Timer, Lock

import rospy
import tf2_ros
from PyKDL import Rotation
from actionlib_msgs.msg import GoalStatus
from tf.transformations import euler_from_quaternion, quaternion_from_euler
from tf2_geometry_msgs import transform_to_kdl
from tf_conversions import posemath
from geometry_msgs.msg import Pose

from robot_command import interfaces

from std_msgs.msg import String
from robot_jog_msgs.srv import (
    CheckPose,
    CheckPoseResponse,
    SetPose,
    SetJoints,
    SetPoseResponse,
    SetJointsResponse,
)
from robot_jog_msgs.msg import JogExecute
from std_msgs.msg import Bool

from robot_common import joint_urdf
from robot_common.tools import get_param
from .interactive_move_base import InteractiveMoveBase


class TargetType:
    PoseTarget = 0
    JointsTarget = 1


JointLimit = namedtuple('JointLimit', 'minimum maximum')


class InteractiveMoveServer(InteractiveMoveBase, TargetType):
    STOP_TIMER_INTERVAL_MS = 100
    TIMEOUT_INTERVAL_MS = 250
    TF_BUFFER_CACHE_TIME_S = 1200
    MIN_SCALING_CORRECTION_FACTOR = 0.005
    JOG_ACCELERATION_SCALE = 0.5

    def __init__(self):
        super().__init__()

        self._tf_buffer = tf2_ros.Buffer(
            cache_time=rospy.Duration.from_sec(self.TF_BUFFER_CACHE_TIME_S)
        )
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer)
        self._moveit = interfaces.MoveItInterface()
        self._joints_to_pose = interfaces.JointsToPoseInterface()
        self._ik = interfaces.IkInterface()
        self._user_frames = interfaces.UserFrameInterface(
            tf_buffer=self._tf_buffer
        )
        self._tool_frames = interfaces.ToolFrameInterface(
            tf_buffer=self._tf_buffer
        )
        self._move_type_interface = interfaces.MoveTypeInterface()
        self._active = False
        self._failed = False
        self._completed = True
        self._start_waiting = (
            False  # start request while something is still running
        )
        self._stop_waiting = False  # used for breaking planning queue
        self._stop_waiting_lock = Lock()
        self._stop_timer = None
        self._timeout_timer = None
        self._targets = [None]  # stores 1 or more targets
        self._continuous = False
        self._planning_frame = self._moveit.pose_reference_frame
        self._tool_frame = self._moveit.tool_reference_frame

        # read joints from urdf to extract joint limits
        base_link = get_param('base_link', 'base_link')
        self._free_joints = joint_urdf.read_robot_description_free_joints(
            base_link=base_link, joint_name_prefix='joint_'
        )
        self._continuous_joint_jog_limit_offset = get_param(
            'continuous_joint_jog_limit_offset', 0.01
        )
        self._continuous_cartesian_jog_lin_target = get_param(
            'continuous_cartesian_jog_lin_target', 5.0
        )
        self._continuous_cartesian_jog_rot_target = get_param(
            'continuous_cartesian_jog_rot_target', pi
        )
        self._joint_limits = {
            k: JointLimit(
                v.minimum + self._continuous_joint_jog_limit_offset,
                v.maximum - self._continuous_joint_jog_limit_offset,
            )
            for k, v in self._free_joints.items()
        }

        # store planners to use and the current active index
        self._planners = []
        self._current_planner_index = 0
        self._total_planning_time = 0.0

        self._moveit.execution_active_changed.append(
            self._on_execution_active_changed
        )
        self._moveit.planning_active_changed.append(
            self._on_planning_active_changed
        )

        self._srvs = [
            rospy.Service(
                self.JOG_OFFSET_SET_POSE_SERVICE,
                SetPose,
                self._jog_offset_set_pose,
            ),
            rospy.Service(
                self.JOG_OFFSET_SET_JOINTS_SERVICE,
                SetJoints,
                self._jog_offset_set_joints,
            ),
            rospy.Service(
                self.JOG_ABSOLUTE_SET_POSE_SERVICE,
                SetPose,
                self._jog_absolute_set_pose,
            ),
            rospy.Service(
                self.JOG_ABSOLUTE_SET_JOINTS_SERVICE,
                SetJoints,
                self._jog_absolute_set_joints,
            ),
            rospy.Service(
                self.JOG_CONTINUOUS_SET_POSE_SERVICE,
                SetPose,
                self._jog_continuous_set_pose,
            ),
            rospy.Service(
                self.JOG_CONTINUOUS_SET_JOINTS_SERVICE,
                SetJoints,
                self._jog_continuous_set_joints,
            ),
            rospy.Service(
                self.JOG_OFFSET_CHECK_POSE_REACHABLE_SERVICE,
                CheckPose,
                self._jog_offset_check_pose_reachable,
            ),
            rospy.Service(
                self.JOG_ABSOLUTE_CHECK_POSE_REACHABLE_SERVICE,
                CheckPose,
                self._jog_absolute_check_pose_reachable,
            ),
        ]
        self._subs = [
            rospy.Subscriber(
                self.JOG_EXECUTE_TOPIC,
                JogExecute,
                self._on_jog_execute_received,
            ),
            rospy.Subscriber(
                self.TOOL_FRAME_TOPIC, String, self._on_tool_frame_received
            ),
        ]
        self._active_pub = rospy.Publisher(
            self.JOG_ACTIVE_TOPIC, Bool, latch=True, queue_size=1
        )
        self._failed_pub = rospy.Publisher(
            self.JOG_FAILED_TOPIC, Bool, latch=True, queue_size=1
        )
        self._completed_pub = rospy.Publisher(
            self.JOG_COMPLETED_TOPIC, Bool, latch=True, queue_size=1
        )

    def shutdown(self):
        self._moveit.shutdown()
        self._joints_to_pose.shutdown()
        self._ik.shutdown()
        self._user_frames.shutdown()
        self._tool_frames.shutdown()
        self._tf_listener.unregister()
        for sub in self._subs:
            sub.unregister()
        self._stop_timeout_timer()
        self._stop_stop_timer()

    def _start(self):
        if self._active:
            self._start_waiting = True
            return
        rospy.logdebug('Starting move')

        accel = self.JOG_ACCELERATION_SCALE
        vel = rospy.get_param(self.JOGRATE_PARAM, 1.0)
        if accel <= 0.0 or vel <= 0.0:
            rospy.logwarn("Can't start jogging with jog rate set to 0.")
            self._set_failed(True)
            return
        self._moveit.max_velocity_scaling_factor = vel
        self._moveit.max_acceleration_scaling_factor = accel

        self._planners = []
        if isinstance(self._targets[-1], Pose):  # lin planner for pose targets
            self._planners.append(self._moveit.LIN_MOVE_PLANNER)
        else:
            self._planners.append(self._moveit.PTP_MOVE_PLANNER)
        if (
            not self._continuous
        ):  # disable PTP and free move for continuous jogs
            if self._moveit.PTP_MOVE_PLANNER not in self._planners:
                self._planners.append(self._moveit.PTP_MOVE_PLANNER)
            self._planners.append(self._moveit.FREE_MOVE_PLANNER)
        self._current_planner_index = 0
        self._total_planning_time = 0.0

        self._set_active(True)
        # TODO: consider changing to a service call
        self._move_type_interface.specify_jog_move()
        self._plan_next()

    def _stop(self):
        self._start_waiting = False
        if not self._active:
            return
        with self._stop_waiting_lock:
            rospy.logdebug('Stopping move')
            self._stop_waiting = True
            self._moveit.stop()
            self._start_stop_timer()

    def _plan_next(self):
        if self._current_planner_index >= len(self._planners):
            return False
        self._planning_start_time = time.time()
        planner = self._planners[self._current_planner_index]
        if planner['pipeline_id'] == 'pilz_industrial_motion_planner':
            self._moveit.set_pilz_industrial_motion_planner_parameters(
                trim_on_failure=self._continuous,
                strict_limits=False,
            )
        if len(self._targets) > 1:
            sequence = [
                self._moveit.create_sequence_item(t, **planner)
                for t in self._targets
            ]
            self._moveit.blend_radius = 0.0
            self._moveit.plan_sequence(sequence, wait=False)
        else:
            self._moveit.plan(self._targets[-1], wait=False, **planner)
        self._current_planner_index += 1
        return True

    def _on_jog_execute_received(self, msg):
        if not (self._completed or self._failed):
            if msg.execute:
                self._start()
                self._start_timeout_timer()
            else:
                self._stop()

    def _on_planning_frame_received(self, msg):
        self._planning_frame = msg.data

    def _on_tool_frame_received(self, msg):
        self._tool_frame = msg.data

    def _on_stop_timer_tick(self, _event):
        if self._active:
            self._stop()
            self._start_stop_timer()
        else:
            self._stop_stop_timer()
            if self._start_waiting:
                self._start()

    def _on_timeout_timer_tick(self, _event):
        rospy.logdebug('Timeout ticked')
        if self._active:
            self._stop()
        self._stop_timeout_timer()

    @staticmethod
    def _modify_pose(ros_pose, modify, compare, **kwargs):
        p = ros_pose.pose.position
        o = ros_pose.pose.orientation
        # convert orientation
        a, b, c = euler_from_quaternion([o.x, o.y, o.z, o.w], axes='sxyz')
        pose = {'x': p.x, 'y': p.y, 'z': p.z, 'a': a, 'b': b, 'c': c}
        new_poses = []
        # modify
        for pose in modify(pose, **kwargs):
            # convert back
            new_pose = deepcopy(ros_pose)
            p = new_pose.pose.position
            o = new_pose.pose.orientation
            q = quaternion_from_euler(
                pose['a'], pose['b'], pose['c'], axes='sxyz'
            )
            o.x, o.y, o.z, o.w = q
            p.x, p.y, p.z = (pose[k] for k in 'xyz')
            new_poses.append(new_pose)
        is_current = compare(ros_pose.pose, new_poses[-1].pose)
        return new_poses, is_current

    def _get_transform(self, frame_id, reference_frame_id, inverse=False):
        target = reference_frame_id
        source = frame_id
        if inverse:
            target, source = source, target
        try:
            return self._tf_buffer.lookup_transform(
                target_frame=target, source_frame=source, time=rospy.Time(0)
            )
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ):
            rospy.logwarn(f'Could not find transform for {frame_id}')
            return None

    def _transform_to_planning_frame(self, pose, planning_frame, tool_frame):
        if planning_frame != self._moveit.pose_reference_frame:
            user_frame_tf = self._get_transform(
                planning_frame, self._moveit.pose_reference_frame, inverse=True
            )
            if not user_frame_tf:
                return None
            pose = posemath.toMsg(
                transform_to_kdl(user_frame_tf) * posemath.fromMsg(pose)
            )

        if tool_frame:
            tool_frame_tf = self._tool_frames.get_transform(tool_frame)
            if not tool_frame_tf:
                return None
            pose = posemath.toMsg(
                posemath.fromMsg(pose) * transform_to_kdl(tool_frame_tf)
            )
        return pose

    def _transform_to_world_frame(self, pose, planning_frame, tool_frame):
        if planning_frame != self._moveit.pose_reference_frame:
            user_frame_tf = self._get_transform(
                planning_frame, self._moveit.pose_reference_frame
            )
            if not user_frame_tf:
                return None
            pose = posemath.toMsg(
                transform_to_kdl(user_frame_tf) * posemath.fromMsg(pose)
            )
        if tool_frame:
            tool_frame_tf = self._tool_frames.get_transform(
                tool_frame, inverse=True
            )
            if not tool_frame_tf:
                return None
            pose = posemath.toMsg(
                posemath.fromMsg(pose) * transform_to_kdl(tool_frame_tf)
            )
        return pose

    def _prepare_pose(self, modify_pose, planning_frame):
        planning_frame = planning_frame or self._user_frames.active_frame_frame
        ros_pose = self._joints_to_pose.get_current_pose()
        tool_frame = self._tool_frames.active_frame
        pose = self._transform_to_planning_frame(
            ros_pose.pose, planning_frame, tool_frame
        )
        if pose is not None:
            ros_pose.pose = pose
        else:
            return None, False, False

        position_tolerance = self._moveit.goal_position_tolerance
        orientation_tolerance = self._moveit.goal_orientation_tolerance
        compare = partial(
            self._moveit.compare_poses,
            position_tolerance=position_tolerance,
            orientation_tolerance=orientation_tolerance,
        )
        try:
            ros_poses, is_current = self._modify_pose(
                ros_pose, modify_pose, compare
            )
        except (KeyError, IndexError):
            return None, False, False

        for ros_pose in ros_poses:
            pose = self._transform_to_world_frame(
                ros_pose.pose, planning_frame, tool_frame
            )
            if pose is not None:
                ros_pose.pose = pose
            else:
                return None, False, is_current

        return [rp.pose for rp in ros_poses], True, is_current

    @staticmethod
    def _offset_modify_pose(pose, req):
        offset_pose = {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'a': 0.0,
            'b': 0.0,
            'c': 0.0,
        }
        for i, name in enumerate(req.axis_names):
            offset_pose[name] = req.values[i]
        # orientations need to be handled differently
        pose['x'] += offset_pose['x']
        pose['y'] += offset_pose['y']
        pose['z'] += offset_pose['z']
        rot = Rotation().EulerZYX(
            offset_pose['c'],
            offset_pose['b'],
            offset_pose['a'],
        ) * Rotation().EulerZYX(pose['c'], pose['b'], pose['a'])
        pose['c'], pose['b'], pose['a'] = rot.GetEulerZYX()
        return [pose]

    @staticmethod
    def _absolute_modify_pose(pose, req):
        for i, name in enumerate(req.axis_names):
            pose[name] = req.values[i]
        return [pose]

    @staticmethod
    def _jog_modify_pose(pose, req):
        poses = [deepcopy(pose)]

        def add_intermediate_steps(name_, target, step):
            targets = []
            current = pose[name_]
            while abs(current - target) > abs(step):
                current += step
                targets.append(current)
            targets.append(target)
            for index, t in enumerate(targets):
                if index >= len(poses):
                    poses.append(deepcopy(poses[-1]))
                poses[index][name_] = t

        for i, name in enumerate(req.axis_names):
            if name in ('a', 'b', 'c'):
                if req.values[i] <= -1:
                    add_intermediate_steps(name, -pi, -pi / 2)
                elif req.values[i] >= 1:
                    add_intermediate_steps(name, pi, pi / 2)
            else:
                if req.values[i] <= -1:
                    poses[-1][name] = -5
                elif req.values[i] >= 1:
                    poses[-1][name] = 5
        return poses

    def _jog_offset_set_pose(self, req):
        ros_poses, success, is_current = self._prepare_pose(
            partial(self._offset_modify_pose, req=req), req.frame_name
        )
        if success:
            self._set_failed(False)
            self._set_completed(False)
            self._targets = ros_poses
            self._continuous = False
        return SetPoseResponse(success=success, is_current=is_current)

    def _jog_absolute_set_pose(self, req):
        ros_poses, success, is_current = self._prepare_pose(
            partial(self._absolute_modify_pose, req=req), req.frame_name
        )
        if success:
            self._set_failed(False)
            self._set_completed(False)
            self._targets = ros_poses
            self._continuous = False
        return SetPoseResponse(success=success, is_current=is_current)

    def _jog_continuous_set_pose(self, req):
        ros_poses, success, is_current = self._prepare_pose(
            partial(self._jog_modify_pose, req=req), req.frame_name
        )
        if success:
            self._set_failed(False)
            self._set_completed(False)
            self._targets = ros_poses
            self._continuous = True
        return SetPoseResponse(success=success, is_current=is_current)

    def _jog_offset_check_pose_reachable(self, req):
        ros_poses, success, is_current = self._prepare_pose(
            partial(self._offset_modify_pose, req=req), req.frame_name
        )
        if success:
            success = self._ik.pose_has_solution(ros_poses[-1], req.frame_name)
        return CheckPoseResponse(success=success, is_current=is_current)

    def _jog_absolute_check_pose_reachable(self, req):
        ros_poses, success, is_current = self._prepare_pose(
            partial(self._absolute_modify_pose, req=req), req.frame_name
        )
        if success:
            success = self._ik.pose_has_solution(ros_poses[-1], req.frame_name)
        return CheckPoseResponse(success=success, is_current=is_current)

    def _set_joints(self, req, modify_joints, continuous):
        joint_state = self._joints_to_pose.get_current_joint_state()
        names = joint_state.name
        values = list(joint_state.position)
        tolerance = self._moveit.goal_joint_tolerance
        jv = {name: req.values[i] for i, name in enumerate(req.joint_names)}
        old_values = values[:]
        modify_joints(values, names, jv)
        is_current = self._moveit.compare_joints(
            old_values, values, tolerance=tolerance
        )
        self._set_failed(False)
        self._set_completed(False)
        self._continuous = continuous
        self._targets = [values]
        return SetJointsResponse(success=True, is_current=is_current)

    def _jog_offset_set_joints(self, req):
        def modify_joints(values, names, jv):
            for i, name in enumerate(names):
                values[i] += jv.get(name, 0.0)
                if name in self._joint_limits:  # clamp to joint limits
                    values[i] = min(
                        self._joint_limits[name].maximum,
                        max(self._joint_limits[name].minimum, values[i]),
                    )

        return self._set_joints(req, modify_joints, False)

    def _jog_absolute_set_joints(self, req):
        def modify_joints(values, names, jv):
            for i, name in enumerate(names):
                values[i] = jv.get(name, values[i])

        return self._set_joints(req, modify_joints, False)

    def _jog_continuous_set_joints(self, req):
        def modify_joints(values, names, jv):
            for i, name in enumerate(names):
                if name not in self._joint_limits:
                    continue
                value = jv.get(name, 0.0)
                if value <= -1.0:
                    values[i] = self._joint_limits[name].minimum
                elif value >= 1.0:
                    values[i] = self._joint_limits[name].maximum

        return self._set_joints(req, modify_joints, True)

    def _set_active(self, value):
        self._active = value
        self._active_pub.publish(Bool(data=value))
        rospy.logdebug(f'Set active {value}')

    def _set_failed(self, value):
        self._failed = value
        self._failed_pub.publish(Bool(data=value))
        rospy.logdebug(f'Set failed {value}')

    def _set_completed(self, value):
        self._completed = value
        self._completed_pub.publish(Bool(data=value))
        rospy.logdebug(f'Set completed {value}')

    def _start_stop_timer(self):
        self._stop_stop_timer()
        self._stop_timer = Timer(
            self.STOP_TIMER_INTERVAL_MS / 1000.0,
            self._on_stop_timer_tick,
        )

    def _stop_stop_timer(self):
        if self._stop_timer:
            self._stop_timer.cancel()
            self._stop_timer = None

    def _start_timeout_timer(self):
        self._stop_timeout_timer()
        self._timeout_timer = Timer(
            self.TIMEOUT_INTERVAL_MS / 1000.0,
            self._on_timeout_timer_tick,
        )

    def _stop_timeout_timer(self):
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

    def _on_execution_active_changed(self, active):
        if active or not self._active:
            return

        if self._moveit.execution_status == GoalStatus.SUCCEEDED:
            self._set_active(False)
            self._set_completed(True)
            rospy.loginfo("move completed")
        else:
            self._set_active(False)
            if not self._stop_waiting:
                self._set_failed(True)
                rospy.loginfo("error executing move")
            else:
                rospy.loginfo("move aborted")
            self._stop_waiting = False

    def _on_planning_active_changed(self, active):
        if active or not self._active:
            return

        # ignore planning time returned by result because it's bogus
        # in case of error
        planning_time = time.time() - self._planning_start_time
        self._total_planning_time += planning_time

        with self._stop_waiting_lock:  # makes sure stop is not
            if self._stop_waiting:
                self._set_active(False)
                self._stop_waiting = False
                rospy.loginfo("aborted planning")
                return

            _success, plan, _, error_details = self._moveit.planning_result
            if self._moveit.planning_status == GoalStatus.SUCCEEDED:
                rospy.loginfo(
                    f"planning succeeded in {self._total_planning_time}s"
                )
                self._moveit.execute(plan, wait=False)
                return

        if not self._plan_next():
            rospy.logwarn(
                f"Could not find planning solution,"
                f" tried {self._total_planning_time:.3f}s,"
                f"{error_details.error_message}"
            )
            self._set_active(False)
            self._set_failed(True)

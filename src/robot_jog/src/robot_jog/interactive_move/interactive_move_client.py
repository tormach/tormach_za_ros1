from threading import Timer

import rospy
from robot_jog_msgs.msg import JogExecute
from robot_jog_msgs.srv import (
    SetPose,
    SetJoints,
    SetPoseRequest,
    SetJointsRequest,
    CheckPose,
    CheckPoseRequest,
)
from std_msgs.msg import Bool

from .interactive_move_base import InteractiveMoveBase
from robot_command.interfaces import (
    ProbeSetupInterfaceSingleton,
    JointTrajectoryErrorContextInterfaceSingleton,
)
from redis_store import ConfigClient

from stop_event_msgs.srv import GetJointTrajectoryErrorContextResponse


class InteractiveMoveClient(InteractiveMoveBase):
    DEFAULT_WAIT_TIMEOUT_S = 10.0
    TIMEOUT_INTERVAL_MS = 150
    IGNORE_PROBE_PARAM = 'user_config/jog/ignoreprobe'

    def __init__(self):
        super().__init__()
        self._active = False
        self._failed = False
        self._completed = False
        self._target_is_current = False
        self._execute_timer = None
        self._probe = ProbeSetupInterfaceSingleton()
        self._error_context = JointTrajectoryErrorContextInterfaceSingleton()
        self._config = ConfigClient(subscribe=True)

        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )

        self._jog_offset_set_pose = rospy.ServiceProxy(
            self.JOG_OFFSET_SET_POSE_SERVICE, SetPose
        )
        self._jog_offset_set_joints = rospy.ServiceProxy(
            self.JOG_OFFSET_SET_JOINTS_SERVICE, SetJoints
        )
        self._jog_absolute_set_pose = rospy.ServiceProxy(
            self.JOG_ABSOLUTE_SET_POSE_SERVICE, SetPose
        )
        self._jog_absolute_set_joints = rospy.ServiceProxy(
            self.JOG_ABSOLUTE_SET_JOINTS_SERVICE, SetJoints
        )
        self._jog_continuous_set_pose = rospy.ServiceProxy(
            self.JOG_CONTINUOUS_SET_POSE_SERVICE, SetPose
        )
        self._jog_continuous_set_joints = rospy.ServiceProxy(
            self.JOG_CONTINUOUS_SET_JOINTS_SERVICE, SetJoints
        )
        self._jog_offset_check_pose_reachable = rospy.ServiceProxy(
            self.JOG_OFFSET_CHECK_POSE_REACHABLE_SERVICE, CheckPose
        )
        self._jog_absolute_check_pose_reachable = rospy.ServiceProxy(
            self.JOG_ABSOLUTE_CHECK_POSE_REACHABLE_SERVICE, CheckPose
        )
        self._jog_absolute_check_pose_reachable.wait_for_service(
            timeout=wait_timeout_s
        )

        self._subs = [
            rospy.Subscriber(
                self.JOG_ACTIVE_TOPIC, Bool, self._on_jog_active_received
            ),
            rospy.Subscriber(
                self.JOG_FAILED_TOPIC, Bool, self._on_jog_failed_received
            ),
            rospy.Subscriber(
                self.JOG_COMPLETED_TOPIC, Bool, self._on_jog_completed_received
            ),
        ]
        self._pub = rospy.Publisher(
            self.JOG_EXECUTE_TOPIC, JogExecute, queue_size=1
        )

    @property
    def active(self):
        return self._active

    @property
    def failed(self):
        return self._failed

    @property
    def completed(self):
        return self._completed

    @property
    def target_is_current(self):
        return self._target_is_current

    def shutdown(self):
        for sub in self._subs:
            sub.unregister()

    def start(self):
        if self.handle_jog_probe_ignore():
            rospy.loginfo("Ignoring probe input during incremental jog move")
        self._pub.publish(JogExecute(execute=True))
        self._start_execute_timer()

    def stop(self):
        self._pub.publish(JogExecute(execute=False))
        self._stop_execute_timer()
        # Poll and report probe errors
        msg = {
            GetJointTrajectoryErrorContextResponse.PROBE_UNEXPECTED_RISING_EDGE: "Unexpected probe contact during jog",
            GetJointTrajectoryErrorContextResponse.PROBE_CONTACT_AT_START: "Can't start a jog motion with probe active. Verify probe connection / polarity, click 'Jog Ignore Probe' to re-enable jogging, then carefully jog the probe to a safe position.",
        }.get(self._error_context.get_error_context(), None)
        if msg:
            rospy.logerr(msg)

    def set_offset_pose_target(self, axis_names, values, frame_name=''):
        req = SetPoseRequest(
            frame_name=frame_name, axis_names=axis_names, values=values
        )
        res = self._jog_offset_set_pose(req)
        self._target_is_current = res.is_current
        return res.success

    def set_absolute_pose_target(self, axis_names, values, frame_name=''):
        req = SetPoseRequest(
            frame_name=frame_name, axis_names=axis_names, values=values
        )
        res = self._jog_absolute_set_pose(req)
        self._target_is_current = res.is_current
        return res.success

    def set_continuous_pose_target(self, axis_names, values, frame_name=''):
        req = SetPoseRequest(
            frame_name=frame_name, axis_names=axis_names, values=values
        )
        res = self._jog_continuous_set_pose(req)
        self._target_is_current = res.is_current
        return res.success

    def check_offset_pose_target_reachable(
        self, axis_names, values, frame_name=''
    ):
        req = CheckPoseRequest(
            frame_name=frame_name, axis_names=axis_names, values=values
        )
        res = self._jog_offset_check_pose_reachable(req)
        self._target_is_current = res.is_current
        return res.success

    def check_absolute_pose_target_reachable(
        self, axis_names, values, frame_name=''
    ):
        req = CheckPoseRequest(
            frame_name=frame_name, axis_names=axis_names, values=values
        )
        res = self._jog_absolute_check_pose_reachable(req)
        self._target_is_current = res.is_current
        return res.success

    def set_offset_joints_target(self, joint_names, values):
        req = SetJointsRequest(joint_names=joint_names, values=values)
        res = self._jog_offset_set_joints(req)
        self._target_is_current = res.is_current
        return res.success

    def set_absolute_joints_target(self, joint_names, values):
        req = SetJointsRequest(joint_names=joint_names, values=values)
        res = self._jog_absolute_set_joints(req)
        self._target_is_current = res.is_current
        return res.success

    def set_continuous_joints_target(self, joint_names, values):
        req = SetJointsRequest(joint_names=joint_names, values=values)
        res = self._jog_continuous_set_joints(req)
        self._target_is_current = res.is_current
        return res.success

    def _on_jog_active_received(self, msg):
        self._active = msg.data

    def _on_jog_failed_received(self, msg):
        self._failed = msg.data

    def _on_jog_completed_received(self, msg):
        self._completed = msg.data

    def _start_execute_timer(self):
        self._stop_execute_timer()
        self._execute_timer = Timer(
            self.TIMEOUT_INTERVAL_MS / 1000.0, self._on_execute_timer_tick
        )
        self._execute_timer.start()

    def _stop_execute_timer(self):
        if self._execute_timer:
            self._execute_timer.cancel()
            self._execute_timer = None
            return True
        return False

    def handle_jog_probe_ignore(self):
        ignore_probe = self._config.get_param(self.IGNORE_PROBE_PARAM)
        if ignore_probe:
            self._probe.set_next_probe_move(6)
            return True
        return False

    def _on_execute_timer_tick(self):
        self._pub.publish(JogExecute(execute=True))
        self._start_execute_timer()

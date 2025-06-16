from threading import Lock

import actionlib
import rospy
from actionlib_msgs.msg import GoalStatus
from control_msgs.msg import (
    GripperCommandAction,
    GripperCommandGoal,
    GripperCommandFeedback,
    GripperCommandResult,
)
from sensor_msgs.msg import JointState
from std_srvs.srv import Empty


class GripperInterface:
    WAIT_TIMEOUT_S = 10.0
    SHORT_WAIT_TIMEOUT_S = 0.01
    CHECK_TIMER_PERIOD_S = 0.2
    GRIPPER_NAME = 'gripper/main'
    GRIPPER_COMMAND_ACTION = f'{GRIPPER_NAME}'
    GRIPPER_CALIBRATE_SERVICE = f'{GRIPPER_NAME}/calibrate'
    GRIPPER_POSITION_FB_TOPIC = f'{GRIPPER_NAME}/position_feedback'

    def __init__(self):
        self._command_result = None
        self._command_active = False
        self._command_active_lock = Lock()
        self._success = False
        self._configured = False
        self._current_position = 0.0

        self.on_current_position_changed_cb = None
        self.on_configured_changed_cb = None
        self.on_success_changed_cb = None
        self.on_command_active_changed_cb = None

        self._command_action = actionlib.SimpleActionClient(
            self.GRIPPER_COMMAND_ACTION, GripperCommandAction
        )
        self._calibrate_srv = rospy.ServiceProxy(
            self.GRIPPER_CALIBRATE_SERVICE, Empty
        )
        self._pos_fb_sub = rospy.Subscriber(
            self.GRIPPER_POSITION_FB_TOPIC, JointState, self._on_pos_fb_received
        )
        # check if gripper action server is available in non-blocking fashion
        self._start_time = rospy.Time.now()
        self._check_timer = rospy.Timer(
            rospy.Duration.from_sec(self.CHECK_TIMER_PERIOD_S),
            self._on_check_timer_ticked,
        )

    def _on_check_timer_ticked(self, event):
        self._check_action_services()
        if self._configured:
            self._check_timer.shutdown()
        elif rospy.Time.now() - self._start_time > rospy.Duration.from_sec(
            self.WAIT_TIMEOUT_S
        ):
            rospy.loginfo(
                "Gripper action server not found. Likely no gripper configured."
            )
            self._check_timer.shutdown()

    def _check_action_services(self):
        started = self._command_action.wait_for_server(
            rospy.Duration.from_sec(self.SHORT_WAIT_TIMEOUT_S)
        )
        try:
            self._calibrate_srv.wait_for_service(
                rospy.Duration.from_sec(self.SHORT_WAIT_TIMEOUT_S)
            )
        except rospy.ROSException:
            started = False
        self._configured = started
        if self.on_configured_changed_cb is not None:
            self.on_configured_changed_cb(self._configured)

    @property
    def command_result(self):
        return self._command_result

    @property
    def command_active(self):
        with self._command_active_lock:
            return self._command_active

    @property
    def success(self):
        return self._success

    @property
    def configured(self):
        return self._configured

    @property
    def current_position(self):
        return self._current_position

    def shutdown(self):
        self._command_action.cancel_all_goals()
        self._calibrate_srv.close()
        self._pos_fb_sub.unregister()

    def calibrate(self):
        self._calibrate_srv()

    def goto_position(self, position, effort=20.0, wait=True):
        goal = GripperCommandGoal()
        goal.command.position = position
        goal.command.max_effort = effort
        self._set_command_active(True)
        self._command_action.send_goal(
            goal,
            active_cb=self._command_active_cb,
            feedback_cb=self._command_feedback_cb,
            done_cb=self._command_done_cb,
        )
        if not wait:
            return None
        while self._command_action.wait_for_result() and self._command_active:
            pass  # wait to prevent race condition in actionlib
        return self._command_result

    def stop(self):
        self._command_action.cancel_all_goals()

    def _set_command_active(self, value):
        with self._command_active_lock:
            self._command_active = value
        if self.on_command_active_changed_cb is not None:
            self.on_command_active_changed_cb(value)

    @staticmethod
    def _command_active_cb():
        rospy.logdebug("Gripper command active")

    @staticmethod
    def _command_feedback_cb(feedback: GripperCommandFeedback):
        rospy.logdebug(
            f"Gripper command feedback: "
            f"pos: {feedback.position}"
            f"effort: {feedback.effort}"
            f"stalled: {feedback.stalled}"
        )

    def _command_done_cb(self, status: int, result: GripperCommandResult):
        self._success = status == GoalStatus.SUCCEEDED
        self._command_result = (
            result.reached_goal,
            result.effort,
            result.position,
            result.stalled,
        )
        self._set_command_active(False)
        if self.on_success_changed_cb is not None:
            self.on_success_changed_cb(self._success)

    def _on_pos_fb_received(self, msg: JointState):
        if len(msg.position) == 0:
            return
        if self._current_position == msg.position[0]:
            return
        self._current_position = msg.position[0]
        if self.on_current_position_changed_cb is not None:
            self.on_current_position_changed_cb(self._current_position)


class GripperInterfaceSingleton:
    """
    Singleton interface for grippers
    """

    _instance = None

    def __init__(self):
        if not GripperInterfaceSingleton._instance:
            GripperInterfaceSingleton._instance = GripperInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        setattr(self._instance, key, value)

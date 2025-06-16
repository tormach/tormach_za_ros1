import logging

from typing import Dict
from threading import Lock

from .feetech import USB2FeetechDevice
from .feetech.udp_feetech_device import UDPFeetechDevice
from .feetech.exceptions import CommunicationError
from .gripper_device import GripperDevice
from .helpers import ConnectPythonLoggingToROS
from std_srvs.srv import Trigger, TriggerResponse
from std_msgs.msg import Bool
import actionlib
from control_msgs.msg import (
    GripperCommandAction,
    GripperCommandResult,
    GripperCommandGoal,
)
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import JointState


import rospy


class GripperControl:
    def __init__(self, name: str, servo_id: int, gripper: GripperDevice):
        self.name = name
        self.servo_id = servo_id
        self._gripper = gripper
        self._lock = Lock()
        self._action_server = actionlib.SimpleActionServer(
            f'~{name}',
            GripperCommandAction,
            self._gripper_action_execute,
            False,
        )
        self._action_server.register_preempt_callback(
            self._gripper_action_preempt
        )
        self._action_server.start()

        self._calibrate_srv = rospy.Service(
            f'~{name}/calibrate', Trigger, self._calibrate_srv
        )

    @property
    def gripper(self):
        with self._lock:
            return self._gripper

    @gripper.setter
    def gripper(self, gripper):
        with self._lock:
            self._gripper = gripper

    def _gripper_action_execute(self, goal: GripperCommandGoal):
        if not self.gripper:
            rospy.logerr("Cannot execute goal: gripper not connected")
            self._action_server.set_aborted()
            return

        rospy.loginfo(
            f"Execute goal: position={goal.command.position:.1f}, "
            f"max_effort={goal.command.max_effort:.1f}"
        )

        if goal.command.max_effort == 0.0:
            rospy.loginfo("Release torque: start")
            succeeded = self.gripper.release()
            rospy.loginfo("Release torque: done")
        else:
            rospy.loginfo("Go to position: start")
            succeeded = self.gripper.goto_position(
                goal.command.position, goal.command.max_effort
            )
            rospy.loginfo(
                f"Go to position: {'done' if succeeded else 'failed'}"
            )

        if not succeeded:
            self.gripper.halt()

        result = GripperCommandResult()
        # not necessarily the current position of the gripper
        # if the gripper did not reach its goal position.
        result.position = self.gripper.get_position()
        result.effort = goal.command.max_effort
        result.stalled = False
        result.reached_goal = succeeded
        self._action_server.set_succeeded(result)

    def _gripper_action_preempt(self):
        if not self.gripper:
            rospy.logerr("Cannot preempt goal: gripper not connected")
            return

        rospy.loginfo("Aborting gripper goal")
        self.gripper.abort()

    def _calibrate_srv(self, _msg):
        if not self.gripper:
            rospy.logerr("Cannot calibrate: gripper not connected")
            return TriggerResponse(success=False)

        rospy.loginfo("Calibrate service: request received")
        res = TriggerResponse()
        if self.gripper.calibrate():
            rospy.loginfo("Calibrate service: request successfully completed")
            res.success = True
        else:
            rospy.loginfo("Calibrate service: calibration failed")
            res.success = False
        return res

    def shutdown(self):
        self._action_server.action_server.stop()
        self._calibrate_srv.shutdown()


class GripperDiagnostics:
    OVERHEATING_TEMPERATURE = 70
    HOT_TEMPERATURE = 65

    def __init__(self, grippers: Dict[str, GripperControl]):
        self._grippers = grippers

        self._pub = rospy.Publisher(
            '/diagnostics', DiagnosticArray, queue_size=1
        )

    def send_diags(self):
        # See diagnostics with: rosrun rqt_runtime_monitor rqt_runtime_monitor
        msg = DiagnosticArray()
        msg.header.stamp = rospy.Time.now()

        for name, gripper_control in self._grippers.items():
            status = DiagnosticStatus()
            status.name = f"Gripper '{name}' servo {gripper_control.servo_id}"
            status.hardware_id = f'{gripper_control.servo_id}'

            if gripper_control.gripper is None:
                status.level = DiagnosticStatus.ERROR
                status.message = 'DISCONNECTED'
                msg.status.append(status)
                continue

            servo = gripper_control.gripper.servo
            temperature = servo.present_temperature
            status.values.append(KeyValue('Temperature', str(temperature)))
            status.values.append(
                KeyValue('Voltage', str(servo.present_input_voltage))
            )
            error_status = ", ".join(
                servo.decode_error_status(servo.cached_error_status)
            )
            status.values.append(KeyValue('Error status', error_status or "OK"))

            if temperature >= self.OVERHEATING_TEMPERATURE:
                status.level = DiagnosticStatus.ERROR
                status.message = 'OVERHEATING'
            elif temperature >= self.HOT_TEMPERATURE:
                status.level = DiagnosticStatus.WARN
                status.message = 'HOT'
            else:
                status.level = DiagnosticStatus.OK
                status.message = 'OK'

            msg.status.append(status)

        self._pub.publish(msg)

    def shutdown(self):
        pass  # nothing to cleanup


class GripperStatus:
    FINGER_OPEN_POS = -0.03
    FINGER_CLOSED_POS = 0.0

    def __init__(self, grippers: Dict[str, GripperControl]):
        self._grippers = grippers
        self._joint_state_pub = rospy.Publisher(
            'joint_states', JointState, queue_size=5
        )
        self._pos_fb_pubs = {}
        for name in self._grippers.keys():
            self._pos_fb_pubs[name] = rospy.Publisher(
                f'~{name}/position_feedback', JointState, queue_size=5
            )

        self._connected_pub = rospy.Publisher(
            f'~{name}/connected', Bool, latch=True, queue_size=1
        )
        self._last_connected = {}

    def publish_status(self):
        state_msg = JointState()
        state_msg.header.stamp = rospy.Time.now()
        for name, gripper_control in self._grippers.items():
            if not gripper_control.gripper:
                pos = 0.0
                connected = False
            else:
                pos = gripper_control.gripper.get_position()
                connected = True
            joint_pos = self.FINGER_OPEN_POS + (100.0 - pos) / 100.0 * (
                self.FINGER_CLOSED_POS - self.FINGER_OPEN_POS
            )
            state_msg.name.append(f'{name}_gripper_body_finger1')
            state_msg.position.append(joint_pos)

            pos_msg = JointState()
            pos_msg.header.stamp = state_msg.header.stamp
            pos_msg.name.append('finger1')
            pos_msg.position.append(pos)
            self._pos_fb_pubs[name].publish(pos_msg)
            if connected is not self._last_connected.get(name, None):
                self._connected_pub.publish(Bool(connected))
                self._last_connected[name] = connected

        self._joint_state_pub.publish(state_msg)

    def shutdown(self):
        pass  # nothing to cleanup


class GripperNode:
    DIAG_UPDATE_INTERVAL_S = 1.0
    DIAG_UPDATE_RATE_HZ = 1.0
    STATUS_UPDATE_INTERVAL_S = 0.2
    STATUS_UPDATE_RATE_HZ = 5.0
    OVERLOAD_CHECK_RATE_HZ = 10.0
    UPDATE_RATE_HZ = 20
    SETUP_RETRY_RATE_HZ = 0.2
    LOG_THROTTLE_RATE_HZ = 60.0

    def __init__(self):
        self.connect_logging()

        rospy.init_node('gripper')
        rospy.loginfo("Gripper driver starting")

        self.mode = rospy.get_param('~mode', 'usb')
        self.host_ip = rospy.get_param('~host_ip', '10.9.0.42')
        self.target_ip = rospy.get_param('~target_ip', '10.9.0.51')
        self.port_name = rospy.get_param('~port', '/dev/ttyUSB0')
        self.baudrate = int(rospy.get_param('~baud', '115200'))
        self.gripper_params = rospy.get_param('~grippers')
        self.auto_calibrate_on_startup = rospy.get_param(
            '~auto_calibrate_on_startup', True
        )
        self.auto_calibrate_on_reconnect = rospy.get_param(
            '~auto_calibrate_on_reconnect', True
        )
        self._inital_connection = True

        self._update_rate = rospy.Rate(self.UPDATE_RATE_HZ)
        self._diag_rate = rospy.Rate(self.DIAG_UPDATE_RATE_HZ)
        self._diag_rate.last_time = rospy.Time()
        self._status_rate = rospy.Rate(self.STATUS_UPDATE_RATE_HZ)
        self._status_rate.last_time = rospy.Time()
        self._setup_rate = rospy.Rate(self.SETUP_RETRY_RATE_HZ)
        self._setup_rate.last_time = rospy.Time()
        self._overload_rate = rospy.Rate(self.OVERLOAD_CHECK_RATE_HZ)
        self._overload_rate.last_time = rospy.Time()

        if self.mode not in ('usb', 'udp'):
            rospy.logfatal(f"Invalid mode '{self.mode}'")
            exit(-1)

        self.gripper_controls = {
            name: GripperControl(name, ids[0], None)
            for name, ids in self.gripper_params.items()
        }
        self.diagnostics = GripperDiagnostics(self.gripper_controls)
        self.status = GripperStatus(self.gripper_controls)

    @staticmethod
    def connect_logging():
        # for more verbosity add 'gr60_gripper.feetech' to the list
        for module in ('gr60_gripper.gripper',):
            logger = logging.getLogger(module)
            # reconnect logging calls which are children of this to the ros log system
            logger.addHandler(ConnectPythonLoggingToROS())
            # logs sent to children of trigger with a level >= this will be redirected to ROS
            logger.setLevel(logging.INFO)

    def _run_setup(self):
        if self._setup_rate.remaining() > rospy.Duration(0):
            return False
        self._setup_rate.sleep()
        try:
            if self.mode == 'usb':
                device = USB2FeetechDevice(
                    self.port_name, baudrate=self.baudrate
                )
            elif self.mode == 'udp':
                device = UDPFeetechDevice(
                    self.host_ip, self.target_ip, baudrate=self.baudrate
                )
        except CommunicationError as e:
            rospy.loginfo_throttle(
                self.LOG_THROTTLE_RATE_HZ,
                f"Could not configure gripper device: {str(e)}. Retrying...",
            )
            return False

        rospy.loginfo("Connected to gripper device")
        # for gripper_name, servo_ids in self.gripper_params.items():
        for gripper_control in self.gripper_controls.values():
            auto_calibrate = (
                self.auto_calibrate_on_startup
                if self._inital_connection
                else self.auto_calibrate_on_reconnect
            )
            gripper = GripperDevice(
                device, gripper_control.name, gripper_control.servo_id
            )
            if auto_calibrate:
                if not gripper.calibrate():
                    rospy.logerr("Gripper auto-calibration failed")
            else:
                rospy.loginfo(
                    "Gripper auto-calibration disabled, run calibration manually"
                )
            gripper_control.gripper = gripper
        return True

    def _update_diags(self):
        if self._diag_rate.remaining() > rospy.Duration(0):
            return True
        self._diag_rate.sleep()
        try:
            self.diagnostics.send_diags()
        except Exception as e:
            rospy.loginfo_throttle(
                self.LOG_THROTTLE_RATE_HZ,
                f"Exception while reading diagnostics: {e}",
            )
            return False
        return True

    def _update_status(self):
        if self._status_rate.remaining() > rospy.Duration(0):
            return True
        self._status_rate.sleep()
        try:
            self.status.publish_status()
        except Exception as e:
            rospy.loginfo_throttle(
                self.LOG_THROTTLE_RATE_HZ,
                f"Exception while publishing status: {e}",
            )
            return False
        return True

    def _check_overload(self):
        if self._overload_rate.remaining() > rospy.Duration(0):
            return True
        self._overload_rate.sleep()
        try:
            for gripper_control in self.gripper_controls.values():
                if not gripper_control.gripper:
                    continue
                gripper_control.gripper.servo.check_overload_and_recover()
        except Exception as e:
            rospy.loginfo_throttle(
                self.LOG_THROTTLE_RATE_HZ,
                f"Exception while checking overload: {e}",
            )
            return False
        return True

    def _cleanup(self):
        for gripper_control in self.gripper_controls.values():
            gripper_control.gripper = None
        self.all_servos = []

    def _shutdown(self):
        for gripper_control in self.gripper_controls.values():
            gripper_control.shutdown()
        self.diagnostics.shutdown()
        self.status.shutdown()

    def run(self):
        is_setup = False
        while not rospy.is_shutdown():
            if not is_setup:
                is_setup = self._run_setup()

            ok = self._update_diags() and self._update_status()
            if is_setup and ok:
                ok |= self._check_overload()

            if is_setup and not ok:
                is_setup = False
                self._cleanup()
                rospy.logwarn("Gripper disconnected, trying to reconnect...")
                self._inital_connection = False

            self._update_rate.sleep()

        rospy.loginfo("Gripper driver exiting")
        self._shutdown()

import logging
import time
from threading import Lock

from .feetech import FeetechServo

logger = logging.getLogger(__name__)


class CalibrationError(Exception):
    pass


class GripperDevice:
    POSITION_MAX = 4095  # griper closed
    POSITION_MIN = 1600  # gripper open
    ANGULAR_RESOLUTION = 1

    TORQUE_LIMIT = 80  # maximum gripper torque in percent
    OVERLOAD_TORQUE = 85  # overload torque in percent
    HOLD_TORQUE = 20  # hold torque in percent
    STARTUP_TORQUE = 5  # minimum startup torque in percent
    CALIBRATION_TORQUE = 50  # torque used for calibration move in percent
    OVERLOAD_PROTECTION_TIME_MS = 1000  # overload protection time in ms
    TARGET_VELOCITY = 7500  # target velocity in steps/s, 7500 max vel
    TARGET_ACCELERATION = 0  # target acceleration in steps/s^2, 0 = unlimited

    _WAIT_CHECK_TIME_S = 0.01

    def __init__(self, device, name, servo_id):
        self.name = name
        self.servo = FeetechServo(
            device, servo_id, exception_on_error_response=False
        )
        self._total_steps = self.POSITION_MAX - self.POSITION_MIN
        self._init_servo(self.servo)
        self._calibrated = False
        self._aborted = False
        self._aborted_lock = Lock()

    @property
    def calibrated(self):
        return self._calibrated

    def abort(self):
        with self._aborted_lock:
            self._aborted = True

    def _is_aborted(self):
        with self._aborted_lock:
            return self._aborted

    def calibrate(self):
        try:
            self._calibrate(self.servo)
        except CalibrationError as e:
            logger.error(str(e))
            self.release()
            return False
        else:
            return True

    def _calibrate(self, servo: FeetechServo, max_homing_iterations=3):
        self._calibrated = False
        logger.info(f"calibrating gripper {self.name}")
        servo.torque_limit = self.CALIBRATION_TORQUE
        servo.min_position_limit = 0
        servo.max_position_limit = 4095
        servo.position_offset = 0

        # move gripper fingers together until they touch
        iterations = 0
        while servo.present_load < (
            90 + self.CALIBRATION_TORQUE
        ):  # present load is 100 + torque limit when closed
            if iterations >= max_homing_iterations:
                raise CalibrationError("calibration failed: homing failed")
            servo.reset_current_position()
            servo.goal_position = 4095
            if not self._wait_for_stop(servo):
                raise CalibrationError(
                    "calibration failed: home move timed out"
                )
            iterations += 1

        # unload the gripper
        servo.torque_enable = False
        if not self._wait_for_no_load(servo):
            raise CalibrationError(
                "calibration failed: could not unload gripper"
            )

        # open the gripper 2048 steps
        servo.reset_current_position()
        servo.goal_position = 0
        servo.torque_limit = self.TORQUE_LIMIT
        if not self._wait_for_stop(servo):
            raise CalibrationError(
                "calibration failed: move to middle position timed out"
            )
        # and set it to the servo middle position
        servo.reset_current_position()
        # then completely open the gripper
        servo.goal_position = self.POSITION_MIN
        if not self._wait_for_stop(servo):
            raise CalibrationError(
                "calibration failed: could not move to open position"
            )
        servo.torque_enable = False
        servo.min_position_limit = self.POSITION_MIN
        self._calibrated = True
        logger.info(f"calibrating gripper {self.name} complete")

    def set_max_effort(self, max_effort):
        torque = self._scale(max_effort, self.TORQUE_LIMIT)
        logger.info(f"setting {torque}")
        self.servo.torque_limit = torque

    def get_position(self):
        position = self.servo.present_position - self.POSITION_MIN
        return 100.0 - self._down_scale(position, self._total_steps)

    def goto_position(self, position, torque=100.0):
        """
        :param position: 0..100%, 0% - closed, 100% - open
        :param closing_torque: 0..100%
        """
        if not self._calibrated:
            logger.error("gripper is not calibrated, aborting move")
            return False
        if torque <= 0.0:
            self.release()
            return True

        servo_position = (
            self._scale(100.0 - position, self._total_steps) + self.POSITION_MIN
        )
        logger.info(
            f"goto position {position} {torque}: servo position {servo_position}"
        )

        # set the max effort for closing move
        # the maximum torque also affects the speed of the move
        self.servo.goal_position = servo_position
        self.set_max_effort(torque)
        if not self._wait_for_stop(self.servo):
            if not self._is_aborted():
                logger.error("goto position failed")
            return False

        # Sets torque to keep gripper in position,
        # but does not apply torque if there is no load.
        # This does not provide continuous grasping torque.
        holding_torque = min(self.HOLD_TORQUE, torque)
        self.set_max_effort(holding_torque)
        logger.info("goto position done")
        return True

    def release(self):
        logger.info("Releasing gripper")
        self.servo.torque_enable = False
        return True

    def open(self):
        return self.goto_position(100)

    def close(self):
        return self.goto_position(0)

    def halt(self):
        logger.info("Halting gripper")
        self.servo.goal_position = self.servo.present_position

    def get_temperature(self):
        return self.servo.present_temperature

    def _init_servo(self, servo: FeetechServo):
        servo.write_lock = False
        servo.max_torque_limit = self.TORQUE_LIMIT
        servo.torque_limit = self.TORQUE_LIMIT
        servo.overload_torque = self.OVERLOAD_TORQUE
        servo.protection_torque = self.HOLD_TORQUE
        servo.minimum_startup_force = self.STARTUP_TORQUE
        servo.overload_protection_time = self.OVERLOAD_PROTECTION_TIME_MS
        servo.work_mode = FeetechServo.WORK_MODE_POSITION_SERVO
        servo.goal_acceleration = self.TARGET_ACCELERATION
        servo.goal_velocity = self.TARGET_VELOCITY
        servo.running_time = 0  # execute as fast as possible
        servo.angular_resolution = self.ANGULAR_RESOLUTION

    def _wait_for_stop(self, servo: FeetechServo, timeout=20.0, stop_delay=3):
        with self._aborted_lock:
            self._aborted = False
        wait_start = time.time()
        last_position = 5000
        stop_count = 0
        while not self._is_aborted():
            current_position = servo.present_position
            if current_position == last_position and not servo.moving_status:
                stop_count += 1
                if stop_count >= stop_delay:
                    return True
            else:
                stop_count = 0
            last_position = current_position
            time.sleep(self._WAIT_CHECK_TIME_S)
            if time.time() - wait_start > timeout:
                logger.warning("wait for stop timed out")
                return False
            if servo.cached_error_status:
                logger.warning(
                    f"servo error while waiting for stop: {servo.decode_error_status(servo.cached_error_status)}"
                )
                return False
        return False

    def _wait_for_no_load(self, servo: FeetechServo, timeout=5.0):
        with self._aborted_lock:
            self._aborted = False
        wait_start = time.time()
        last_load = 1000
        while not self._is_aborted():
            current_load = servo.present_load
            if current_load == last_load and current_load == 0:
                return True
            last_load = current_load
            time.sleep(self._WAIT_CHECK_TIME_S)
            if time.time() - wait_start > timeout:
                logger.warning("wait for no load timed out")
                return False
            if servo.cached_error_status:
                logger.warning(
                    f"servo error while waiting for no load: {servo.decode_error_status(servo.cached_error_status)}"
                )
                return False
        return False

    @staticmethod
    def _scale(n, to_max):
        # Scale from 0..100 to 0..to_max
        result = int(n * to_max / 100)
        result = min(result, to_max)
        result = max(result, 0)
        return result

    @staticmethod
    def _down_scale(n, to_max):
        # Scale from 0..to_max to 0..100
        result = int(round(n * 100.0 / to_max))
        result = min(result, 100)
        return max(result, 0)

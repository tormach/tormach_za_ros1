import rospy
from stop_event_msgs.srv import (
    GetJointTrajectoryErrorContext,
    GetJointTrajectoryErrorContextRequest,
    GetJointTrajectoryErrorContextResponse as ECResp,
)

from . import (
    JointsToPoseInterfaceSingleton,
)


class JointTrajectoryErrorContextInterface:
    ERROR_CONTEXT_SERVICE = 'position_trajectory_controller/error_context'
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(self):
        self._joints_to_pose = JointsToPoseInterfaceSingleton()
        self._error_context = rospy.ServiceProxy(
            self.ERROR_CONTEXT_SERVICE, GetJointTrajectoryErrorContext
        )

        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._error_context.wait_for_service(timeout=wait_timeout_s)

    def shutdown(self):
        pass  # nothing to do

    def get_error_context(self):
        # TODO handle exceptions if the service fails?
        response = self._error_context(GetJointTrajectoryErrorContextRequest())
        return response.error_code

    _errstr_map = {
        ECResp.SUCCESSFUL: "Completed successfully",
        ECResp.PATH_TOLERANCE_VIOLATED: "Path tolerance violation",
        ECResp.GOAL_TOLERANCE_VIOLATED: "Goal tolerance violation",
        ECResp.PROBE_UNEXPECTED_RISING_EDGE: "Unexpected probe rising edge",
        ECResp.PROBE_UNEXPECTED_FALLING_EDGE: "Unexpected probe falling edge",
        ECResp.PROBE_CONTACT_AT_START: "Probe active at start of move",
        ECResp.PROBE_INVALID_STATE: "Unhandled probe status",
        ECResp.PROBE_REACHED_MOTION_END: "Motion completed but probe inactive",
        ECResp.HARDWARE_STOP_EVENT: "Hardware soft stop event",
        ECResp.HARDWARE_ESTOP_EVENT: "Hardware emergency stop event",
    }

    def get_error_message(self, error_code=None):
        if error_code is None:
            error_code = self.get_error_context()
        return self._errstr_map.get(
            error_code, f"Unhandled controller error {error_code}"
        )


class JointTrajectoryErrorContextInterfaceSingleton:
    """
    Singleton wrapper for probe setup interfaces in robot controller.
    """

    _instance = None

    def __init__(self):
        if not JointTrajectoryErrorContextInterfaceSingleton._instance:
            JointTrajectoryErrorContextInterfaceSingleton._instance = (
                JointTrajectoryErrorContextInterface()
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

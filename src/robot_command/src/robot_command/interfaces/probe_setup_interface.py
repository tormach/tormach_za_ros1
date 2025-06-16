import rospy
from stop_event_msgs.srv import (
    SetNextProbeMove,
    SetNextProbeMoveRequest,
    GetStopEventResult,
    GetStopEventResultRequest,
)

from . import (
    JointsToPoseInterfaceSingleton,
    ConfigInterfaceSingleton,
    PoseConversionInterfaceSingleton,
)

from ..rpl import (
    Joints,
    Pose,
)


class ProbeSetupInterface:
    SET_PROBING_SERVICE = 'position_trajectory_controller/probe'
    PROBE_RESULT_SERVICE = 'position_trajectory_controller/probe_result'
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(self):
        self._joints_to_pose = JointsToPoseInterfaceSingleton()
        self._pose_conversion = PoseConversionInterfaceSingleton()
        self._probe = rospy.ServiceProxy(
            self.SET_PROBING_SERVICE, SetNextProbeMove
        )
        self._probe_result = rospy.ServiceProxy(
            self.PROBE_RESULT_SERVICE, GetStopEventResult
        )

        self._config = ConfigInterfaceSingleton()

        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._probe.wait_for_service(timeout=wait_timeout_s)
        self._probe_result.wait_for_service(timeout=wait_timeout_s)

    def shutdown(self):
        pass  # nothing to do

    def set_next_probe_move(
        self,
        probe_type,
    ):
        request = SetNextProbeMoveRequest(
            probe_type,
        )
        self._probe(request)

    def get_probe_result(
        self,
    ):
        request = GetStopEventResultRequest()
        response = self._probe_result(request)
        if not response.stop_event:
            # No valid result
            return None

        if response.event_position:
            pose = Pose.from_ros_pose(
                self._joints_to_pose.get_pose_from_joint_values(
                    list(response.event_position)
                )
            ).from_ros_units(
                self._config.linear_unit, self._config.angular_unit
            )
            pose = self._pose_conversion.convert_global_to_tool_pose(pose)
        else:
            pose = None

        return (
            response.stop_event,
            response.event_time,
            # First 6 joints are real joints, 7 and 8 are TCP
            Joints.from_list(response.event_position[:6]),
            pose,
        )


class ProbeSetupInterfaceSingleton:
    """
    Singleton wrapper for probe setup interfaces in robot controller.
    """

    _instance = None

    def __init__(self):
        if not ProbeSetupInterfaceSingleton._instance:
            ProbeSetupInterfaceSingleton._instance = ProbeSetupInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

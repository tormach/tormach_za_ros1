from typing import List

import rospy
from cartesian_state_msgs.srv import (
    GetPose,
    GetPoseRequest,
    GetCurrentPose,
    GetCurrentJointValues,
    GetCurrentPoseRequest,
    GetCurrentJointValuesRequest,
)
from geometry_msgs.msg import Pose, PoseStamped
from sensor_msgs.msg import JointState


class JointsToPoseInterface:
    GET_POSE_SERVICE = 'joints_to_pose/get_pose'
    GET_CURRENT_POSE_SERVICE = 'joints_to_pose/get_current_pose'
    GET_CURRENT_JOINT_VALUES_SERVICE = 'joints_to_pose/get_current_joint_values'
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(self):
        self.tool_reference_frame = rospy.get_param(
            'moveit/tool_reference_frame', 'tool0'
        )
        self.pose_reference_frame = rospy.get_param(
            'moveit/pose_reference_frame', 'world'
        )

        self._get_pose = rospy.ServiceProxy(self.GET_POSE_SERVICE, GetPose)
        self._get_current_pose = rospy.ServiceProxy(
            self.GET_CURRENT_POSE_SERVICE, GetCurrentPose
        )
        self._get_current_joint_values = rospy.ServiceProxy(
            self.GET_CURRENT_JOINT_VALUES_SERVICE, GetCurrentJointValues
        )
        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._get_pose.wait_for_service(timeout=wait_timeout_s)
        self._get_current_pose.wait_for_service(timeout=wait_timeout_s)
        self._get_current_joint_values.wait_for_service(timeout=wait_timeout_s)

    def shutdown(self):
        pass  # nothing to do

    def get_pose_from_joint_values(
        self,
        joints: List[float],
        tool_frame: str = None,
        base_frame: str = None,
    ) -> Pose:
        if not tool_frame:
            tool_frame = self.tool_reference_frame
        if not base_frame:
            base_frame = self.pose_reference_frame

        # Hotfix: use only first 6 joints
        joints = joints[:6]

        request = GetPoseRequest(
            joint_state=JointState(position=joints),
            tool_frame_id=tool_frame,
            base_frame_id=base_frame,
        )
        response = self._get_pose(request)
        return response.pose

    def get_current_pose(
        self,
        tool_frame: str = None,
        base_frame: str = None,
    ) -> PoseStamped:
        if not tool_frame:
            tool_frame = self.tool_reference_frame
        if not base_frame:
            base_frame = self.pose_reference_frame
        request = GetCurrentPoseRequest(
            tool_frame_id=tool_frame, base_frame_id=base_frame
        )
        response = self._get_current_pose(request)
        return response.pose

    def get_current_joint_values(self) -> List[float]:
        request = GetCurrentJointValuesRequest()
        response = self._get_current_joint_values(request)
        return response.joint_state.position

    def get_current_joint_state(self) -> JointState:
        request = GetCurrentJointValuesRequest()
        response = self._get_current_joint_values(request)
        return response.joint_state


class JointsToPoseInterfaceSingleton:
    """
    Singleton interface class query poses from joint states.
    """

    _instance = None

    def __init__(self):
        if not JointsToPoseInterfaceSingleton._instance:
            JointsToPoseInterfaceSingleton._instance = JointsToPoseInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

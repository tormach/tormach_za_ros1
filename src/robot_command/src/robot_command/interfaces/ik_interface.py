import rospy
from geometry_msgs.msg import PoseStamped

from moveit_msgs.msg import MoveItErrorCodes
from moveit_msgs.srv import (
    GetPositionIK,
    GetPositionIKRequest,
    GetPositionIKResponse,
)


class IkInterface:
    IK_REQUEST_SERVICE = '/compute_ik'
    SERVICE_TIMEOUT_S = 10.0

    def __init__(self):
        self.group_name = rospy.get_param('moveit/move_group', None)
        if self.group_name is None:
            raise RuntimeError("ROS param 'moveit/move_group' unset")
        self.tool_reference_frame = rospy.get_param(
            'moveit/tool_reference_frame', None
        )
        if self.tool_reference_frame is None:
            raise RuntimeError("ROS param 'moveit/tool_reference_frame' unset")
        self.pose_reference_frame = rospy.get_param(
            'moveit/pose_reference_frame', None
        )
        if self.pose_reference_frame is None:
            raise RuntimeError("ROS param 'moveit/pose_reference_frame' unset")
        self.solver_timeout_s = rospy.get_param(
            f'move_group/{self.group_name}/kinematics_solver_timeout', 0.005
        )

        self._compute_ik = rospy.ServiceProxy(
            self.IK_REQUEST_SERVICE, GetPositionIK
        )
        self._compute_ik.wait_for_service(timeout=self.SERVICE_TIMEOUT_S)

    def shutdown(self):
        pass  # nothing to do

    def compute_solution_for_pose(self, pose, planning_frame=''):
        pose_stamped = PoseStamped()
        pose_stamped.header.frame_id = (
            planning_frame or self.pose_reference_frame
        )
        pose_stamped.pose = pose
        req = GetPositionIKRequest()
        req.ik_request.timeout = rospy.Duration.from_sec(self.solver_timeout_s)
        req.ik_request.avoid_collisions = True
        req.ik_request.group_name = self.group_name
        req.ik_request.ik_link_name = self.tool_reference_frame
        req.ik_request.pose_stamped = pose_stamped
        req.ik_request.robot_state.is_diff = True
        try:
            response: GetPositionIKResponse = self._compute_ik(req)
            return response
        except rospy.ServiceException as e:
            rospy.logerr(f"Error calculating IK solution {e}")
            return None

    def pose_has_solution(self, pose, planning_frame=''):
        result = self.compute_solution_for_pose(pose, planning_frame)
        return (
            result is not None
            and result.error_code.val == MoveItErrorCodes.SUCCESS
        )


class IkInterfaceSingleton:
    """
    Singleton interface class to calculate ik solutions for poses.
    """

    _instance = None

    def __init__(self):
        if not IkInterfaceSingleton._instance:
            IkInterfaceSingleton._instance = IkInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

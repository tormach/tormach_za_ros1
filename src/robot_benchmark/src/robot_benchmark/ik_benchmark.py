import rospy
from moveit_msgs.msg import MoveItErrorCodes

from moveit_msgs.srv import (
    GetPositionIK,
    GetPositionIKRequest,
    GetPositionIKResponse,
)


class IkBenchmark:
    IK_REQUEST_SERVICE = '/compute_ik'
    SERVICE_WAIT_TIMEOUT_S = 5.0

    def __init__(self, group_name, tool_frame):
        self._compute_ik = rospy.ServiceProxy(
            self.IK_REQUEST_SERVICE, GetPositionIK, persistent=True
        )
        self._compute_ik.wait_for_service(timeout=self.SERVICE_WAIT_TIMEOUT_S)

        self._group_name = group_name
        self._tool_frame = tool_frame

    def run(self, poses):
        successful = 0
        results = []
        for pose in poses:
            success, solution = self._compute_ik_for_pose(pose)
            successful += success
            results.append((pose, success, solution))
        return results

    def shutdown(self):
        pass

    def _compute_ik_for_pose(self, pose):
        req = GetPositionIKRequest()
        req.ik_request.timeout = rospy.Duration.from_sec(0.005)
        req.ik_request.avoid_collisions = True
        req.ik_request.group_name = self._group_name
        req.ik_request.ik_link_name = self._tool_frame
        req.ik_request.pose_stamped = pose
        req.ik_request.robot_state.is_diff = True
        try:
            response: GetPositionIKResponse = self._compute_ik(req)
            return (
                response.error_code.val == MoveItErrorCodes.SUCCESS,
                response.solution,
            )
        except rospy.ServiceException as e:
            print(f"error {e}")
            return False

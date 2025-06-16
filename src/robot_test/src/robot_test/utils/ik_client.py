#!/usr/bin/env python
import rospy

from geometry_msgs.msg import Pose as RosPose

# from geometry_msgs.msg import Vector3, Quaternion
from tf.transformations import quaternion_from_euler

# from tf.transformations import euler_from_quaternion


from movej_ik_server_msgs.srv import (
    MovejClosestIKService,
    MovejClosestIKServiceRequest,
    MovejUserIKService,
    MovejUserIKServiceRequest,
    GetArmConfigService,
    GetArmConfigServiceRequest,
)

from movej_ik_server_msgs.msg import ArmConfigs


def ros_pose_from_trpl_pose(goal_pose):
    # note that units are meters and rad
    x = goal_pose[0]
    y = goal_pose[1]
    z = goal_pose[2]
    a = goal_pose[3]
    b = goal_pose[4]
    c = goal_pose[5]

    ros_pose = RosPose()
    ros_pose.position.x = x
    ros_pose.position.y = y
    ros_pose.position.z = z

    q = quaternion_from_euler(a, b, c, axes='sxyz')

    ros_pose.orientation.x = q[0]
    ros_pose.orientation.y = q[1]
    ros_pose.orientation.z = q[2]
    ros_pose.orientation.w = q[3]
    return ros_pose


class IKClient:
    def __init__(self):
        # rospy.init_node('robot_config_client')
        rospy.wait_for_service('/movej_closest_ik_service')
        rospy.wait_for_service('/movej_user_ik_service')
        rospy.wait_for_service('/arm_config_service')

        self.move_closest_ik_service = rospy.ServiceProxy(
            '/movej_closest_ik_service', MovejClosestIKService
        )

        self.move_user_ik_service = rospy.ServiceProxy(
            '/movej_user_ik_service', MovejUserIKService
        )

        self.get_arm_config_service = rospy.ServiceProxy(
            '/arm_config_service', GetArmConfigService
        )

    def send_closest_service_request(
        self, goal_pose, arm_config=ArmConfigs.ANY_ARM_CONFIG
    ):
        service_request = MovejClosestIKServiceRequest()

        ros_pose = ros_pose_from_trpl_pose(goal_pose)

        service_request.pose = ros_pose
        service_request.arm_config = arm_config

        response = self.move_closest_ik_service(service_request)

        return response

    def send_user_service_request(
        self, goal_pose, arm_config, rev_count, cached_joints=[]
    ):
        service_request = MovejUserIKServiceRequest()

        ros_pose = ros_pose_from_trpl_pose(goal_pose)

        service_request.pose = ros_pose
        service_request.arm_config = arm_config
        service_request.rev_count = rev_count
        service_request.cached_joints = cached_joints

        response = self.move_user_ik_service(service_request)

        return response

    def get_config(self):
        service_request = GetArmConfigServiceRequest()
        service_request.use_current_pose = True

        print('Sending service request to /arm_config_service...')
        response = self.move_ik_service(service_request)
        return response.arm_config, response.rev_count

#!/usr/bin/env python
import rospy
from movej_ik_server_msgs.srv import (
    GetArmConfigService,
    GetArmConfigServiceRequest,
)


class ArmConfigHandler:
    def __init__(self):
        # rospy.init_node('robot_config_client')
        rospy.wait_for_service('/arm_config_service')
        self.move_ik_service = rospy.ServiceProxy(
            '/arm_config_service', GetArmConfigService
        )

    def get_config(self):
        service_request = GetArmConfigServiceRequest()
        service_request.joint_values = []

        print('Sending service request to /arm_config_service...')
        response = self.move_ik_service(service_request)
        return response.arm_config, response.rev_count

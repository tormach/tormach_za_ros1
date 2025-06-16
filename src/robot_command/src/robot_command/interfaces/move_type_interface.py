#!/usr/bin/env python

import rospy
from velocity_override_msgs.srv import MoveTypeService, MoveTypeServiceRequest
from velocity_override_msgs.msg import MoveTypes, ServiceNames


class MoveTypeInterface:
    def __init__(self):
        service_name = ServiceNames.NEXT_MOVE_SERVICE_NAME
        rospy.wait_for_service(service_name)
        self.move_type_service_client = rospy.ServiceProxy(
            service_name, MoveTypeService
        )

    def specify_program_move(self, velocity_scale):
        try:
            request = MoveTypeServiceRequest()
            request.move_type = MoveTypes.PROGRAM_MOVE
            request.velocity_scale = velocity_scale
            response = self.move_type_service_client(request)
            return response.success
        except rospy.ServiceException as e:
            rospy.logerr(f"Service call failed: {e}")
            return False

    def specify_jog_move(self):
        try:
            request = MoveTypeServiceRequest()
            request.move_type = MoveTypes.JOG
            request.velocity_scale = 1.0
            response = self.move_type_service_client(request)
            return response.success
        except rospy.ServiceException as e:
            rospy.logerr(f"Service call failed: {e}")
            return False


class MoveTypeInterfaceSingleton:
    """
    Singleton interface to feedhold
    """

    _instance = None

    def __init__(self):
        if not MoveTypeInterfaceSingleton._instance:
            MoveTypeInterfaceSingleton._instance = MoveTypeInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)


if __name__ == '__main__':
    rospy.init_node('move_type_client')
    print("Client node initialized.")

    move_interface = MoveTypeInterface()

    result1 = move_interface.specify_program_move(0.5)
    print(f"Program move was {'successful' if result1 else 'unsuccessful'}.")

    result2 = move_interface.specify_jog_move()
    print(f"Jog move was {'successful' if result2 else 'unsuccessful'}.")

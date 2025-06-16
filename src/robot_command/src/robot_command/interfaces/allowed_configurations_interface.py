import rospy

from movej_ik_server_msgs.srv import (
    SetArmConfigConstraintsService,
    SetArmConfigConstraintsServiceRequest,
    SetArmConfigConstraintsServiceResponse,
)


class AllowedConfigurationsInterface:
    CONFIGURATIONS_REQUEST_SERVICE = '/arm_config_constraint_service'
    SERVICE_TIMEOUT_S = 10.0

    def __init__(self):
        self._set_allowed_config = rospy.ServiceProxy(
            self.CONFIGURATIONS_REQUEST_SERVICE, SetArmConfigConstraintsService
        )
        self._set_allowed_config.wait_for_service(
            timeout=self.SERVICE_TIMEOUT_S
        )

    def shutdown(self):
        pass  # nothing to do

    def set_allowed_constraints(self, config_mask):
        req = SetArmConfigConstraintsServiceRequest()
        req.allowed_arm_configs_mask = config_mask
        try:
            response: SetArmConfigConstraintsServiceResponse = (
                self._set_allowed_config(req)
            )
            return response
        except rospy.ServiceException as e:
            rospy.logerr(f"Error setting Arm Constraints {e}")
            return None


class AllowedConfigurationsInterfaceSingleton:
    """
    Singleton interface to set allowed configurations.
    """

    _instance = None

    def __init__(self):
        if not AllowedConfigurationsInterfaceSingleton._instance:
            AllowedConfigurationsInterfaceSingleton._instance = (
                AllowedConfigurationsInterface()
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

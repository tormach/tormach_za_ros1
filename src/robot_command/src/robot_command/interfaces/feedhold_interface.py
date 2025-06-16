#!/usr/bin/env python

import rospy
from velocity_override_msgs.srv import FeedholdStatusService


class FeedholdInterface:
    FEEDHOLD_SERVICE_NAME = "/feedhold_status"

    def __init__(self):
        self.client = rospy.ServiceProxy(
            self.FEEDHOLD_SERVICE_NAME, FeedholdStatusService
        )
        self.client.wait_for_service()

    def toggle_feedhold(self, feedhold_setting: bool):
        try:
            response = self.client(feedhold_setting)
            if response.success:
                if feedhold_setting:
                    rospy.loginfo("Successfully set feedhold.")
                else:
                    rospy.loginfo("Successfully unset feedhold.")
            else:
                if feedhold_setting:
                    rospy.logwarn("Failed to set feedhold.")
                else:
                    rospy.logwarn("Failed to unset feedhold.")
        except rospy.ServiceException as e:
            rospy.logerr(f"Service call failed: {e}")


class FeedholdInterfaceSingleton:
    """
    Singleton interface to feedhold
    """

    _instance = None

    def __init__(self):
        if not FeedholdInterfaceSingleton._instance:
            FeedholdInterfaceSingleton._instance = FeedholdInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)


if __name__ == "__main__":
    feedhold_client = FeedholdInterface()

    feedhold_client.setFeedhold()
    rospy.sleep(1)
    feedhold_client.unsetFeedhold()

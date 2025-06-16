import rospy

NODE_NAME = 'interpreter_process_node'


class RosNodeInterface:
    def __init__(self):
        try:
            del rospy.names.get_mappings()[
                '__name'
            ]  # clean any name mappings for subprocess
        except KeyError:
            pass
        rospy.init_node(NODE_NAME, anonymous=True)

    def shutdown(self):
        pass  # nothing to stop


class RosNodeInterfaceSingleton:
    """
    Singleton interface class to ROS node
    """

    _instance = None

    def __init__(self):
        if not RosNodeInterfaceSingleton._instance:
            RosNodeInterfaceSingleton._instance = RosNodeInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

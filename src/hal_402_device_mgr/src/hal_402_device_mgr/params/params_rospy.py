import rospy
import rosgraph
from .params_yaml import EtherCATYAMLParams


class EtherCATROSParams(EtherCATYAMLParams):
    def __init__(self, group):
        self.group = group

    def load_all_params(self):
        if not rosgraph.is_master_online():
            raise ConnectionRefusedError(
                "Unable to read ROS params:  ROS master offline"
            )
        return rospy.get_param(self.param_top_level_key)

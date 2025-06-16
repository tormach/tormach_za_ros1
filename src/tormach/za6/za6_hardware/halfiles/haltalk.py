from hal_hw_interface import hal
import rospy

if rospy.get_param("/hal_hardware/sim_mode", True):
    hal.loadusr('haltalk', wait=True)

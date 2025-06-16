from hal_hw_interface import hal
import rospy


def load_hal_io_component():
    # Load hal_io user component
    cmd = 'rosrun --debug hal_hw_interface hal_io'
    rospy.loginfo(f"Starting hal_io component, cmd: '{cmd}'")
    wait_timeout_s = rospy.get_param('ros_wait_timeout_s', 30)
    hal.loadusr(cmd, wait=True, wait_name='hal_io', wait_timeout=wait_timeout_s)
    rospy.loginfo("Successfully started hal_io component")


load_hal_io_component()

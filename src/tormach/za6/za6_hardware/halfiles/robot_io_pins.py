from hal_hw_interface import hal
import rospy


def load_dry_run_switcher_component():
    # Load dry_run_switcher user component
    cmd = 'rosrun za6_hardware dry_run_switcher'
    rospy.loginfo(f"Starting dry_run_switcher component, cmd: '{cmd}'")
    wait_timeout_s = rospy.get_param('ros_wait_timeout_s', 30)
    hal.loadusr(
        cmd,
        wait=True,
        wait_name='dry_run_switcher',
        wait_timeout=wait_timeout_s,
    )
    rospy.loginfo("Successfully started dry_run_switcher component")


load_dry_run_switcher_component()

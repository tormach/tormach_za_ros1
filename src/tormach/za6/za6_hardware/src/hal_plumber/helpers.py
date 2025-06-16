import rospy
import time


def wait_for_param(name, timeout=1.0):
    while not rospy.has_param(name) and timeout > 0:
        time.sleep(0.01)
        timeout -= 0.01
    if timeout <= 0:
        raise RuntimeError(f'Parameter {name} not found, check redis_store.')
    return rospy.get_param(name)

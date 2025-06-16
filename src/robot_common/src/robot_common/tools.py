import rospy


def get_param(name, value=None):
    private = f"~{name}"
    if rospy.has_param(private):
        return rospy.get_param(private)
    elif rospy.has_param(name):
        return rospy.get_param(name)
    else:
        return value

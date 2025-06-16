import rospy


def deprecated_command(cls, old_name):
    new_name = cls.name

    class DeprecatedCommand(cls):
        name = old_name

        def __init__(self, *args, **kwargs):
            rospy.logwarn(
                f"Command \"{self.name}\" is deprecated, use \"{new_name}\" instead."
            )
            super().__init__(*args, **kwargs)

    return DeprecatedCommand

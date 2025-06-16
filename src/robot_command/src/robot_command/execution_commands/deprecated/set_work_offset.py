import rospy

from ..set_user_frame import SetUserFrame


class SetWorkOffset(SetUserFrame):
    name = 'set_work_offset'

    def execute(self) -> None:
        rospy.logwarn(f"{self.name}")
        super().execute()

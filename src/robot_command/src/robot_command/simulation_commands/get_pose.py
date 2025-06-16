import time

from ..rpl import Command, Pose
from .constants import SLEEP_TIME


class GetPose(Command):
    name = 'get_pose'

    def __init__(
        self, apply_user_frame: bool = True, apply_tool_frame: bool = True
    ):
        super().__init__()

        self.apply_user_frame = apply_user_frame
        self.apply_tool_frame = apply_tool_frame

    def execute(self):
        print(f'executing {self.name}')
        time.sleep(SLEEP_TIME)
        return Pose()

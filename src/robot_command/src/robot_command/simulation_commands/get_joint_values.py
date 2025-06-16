import time

from ..rpl import Command, Joints
from .constants import SLEEP_TIME


class GetJointValues(Command):
    name = 'get_joint_values'

    def __init__(self):
        super().__init__()

    def execute(self):
        print(f'executing {self.name}')
        time.sleep(SLEEP_TIME)
        return Joints()

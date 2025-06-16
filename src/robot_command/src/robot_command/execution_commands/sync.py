import time
import rospy

from ..rpl import Command
from .constants import SYNC_TIME


class Sync(Command):
    name = 'sync'

    def __init__(self):
        """
        The sync command is used in wait cycles and to force the execution of queued
        move commands.
        """
        super().__init__()

    def execute(self) -> None:
        rospy.logdebug_throttle(0.5, 'executing sync')
        time.sleep(SYNC_TIME)

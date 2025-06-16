import time

from ..rpl import Command
from .constants import SYNC_TIME


class Sync(Command):
    name = 'sync'

    def __init__(self):
        super().__init__()

    def execute(self):
        print('executing sync')
        time.sleep(SYNC_TIME)

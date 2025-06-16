from enum import IntEnum

import rospy

from hal_hw_interface import hal, rtapi


class HALPlumberBase:
    """
    Base class for everything else; basically exists to provide a mechanism for
    adding HAL functions in the right order
    """

    class Prio(IntEnum):
        # Conventions for where to add update commands in thread
        LIST_HEAD = 0  # The head of the thread linked list
        DRIVE_READ_FB = 100  # Read fb from drive
        SAFETY_CHAIN = 300  # Check safety conditions
        FB_CHAIN = 400  # Process fb
        ROS_CONTROL = 500  # ros_control read(); update(); write()
        CMD_CHAIN = 700  # Process cmd
        DRIVE_WRITE_CMD = 900  # Write cmd to drive
        LIST_TAIL = 10000  # The tail of the thread linked list

    def __init__(self, thread_name, thread_period, prefix):
        self.thread_name = thread_name
        self.thread_period = thread_period
        self.prefix = prefix
        self.thread_functs = {}  # A dict with prio:func_name mappings

    def func_config(self, name, prio):
        if prio in self.thread_functs:
            raise RuntimeError(
                f"Function '{self.thread_functs[prio]}' already set with prio {prio}"
            )
        self.thread_functs[prio] = name

    def newinst(self, comp_name, name, *args, **kwargs):
        real_name = self.prefix + name
        return rtapi.newinst(comp_name, real_name, *args, **kwargs)

    def newsig(self, name, type, *args, **kwargs):
        real_name = self.prefix + name
        return hal.newsig(real_name, type, *args, **kwargs)

    def signal(self, name):
        return hal.Signal(self.prefix + name)

    def comp(self, name):
        real_name = self.prefix + name
        if real_name in hal.components:
            return hal.components[real_name]
        else:
            return hal.instances[real_name]

    def add_funcs(self):
        # Call HAL addf for each function in correct thread order
        for prio in sorted(self.thread_functs.keys()):
            rospy.loginfo(f"Adding HAL function {self.thread_functs[prio]}")
            hal.addf(self.thread_functs[prio], self.thread_name)

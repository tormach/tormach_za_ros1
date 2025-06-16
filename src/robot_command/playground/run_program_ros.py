#!/usr/bin/env python
import time

import rospy
from robot_command_msgs.msg import InterpreterState
from robot_command_msgs.msg import ProgramPosition

from robot_command.commander import Commander
from robot_command.rpl import CommandInterpreter


class RobotCommandInterpreter:
    def __init__(self):
        CommandInterpreter.status_report_cb = self._publish_state
        self._commander = Commander()

        self._pub = rospy.Publisher(
            '/robot_command/interpreter_state', InterpreterState, queue_size=1
        )

    def load_program(self, path):
        self._commander.load_program(path)

    def execute(self):
        self._commander.start_program()

    def _publish_state(self, command):
        position = command.position
        msg = InterpreterState()
        msg.position = ProgramPosition(
            line_number=position.linum, filename=position.filename
        )
        self._pub.publish(msg)


def start_interpreter(name, path):
    rospy.init_node(name, anonymous=True)
    interpreter = RobotCommandInterpreter()
    time.sleep(0.5)  # wait for publisher to settle
    interpreter.load_program(path)
    interpreter.execute()


if __name__ == '__main__':
    start_interpreter('interpreter_instance', './test_program3.py')

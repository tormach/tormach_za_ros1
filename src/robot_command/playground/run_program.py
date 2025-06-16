#!/usr/bin/env python
import rospy

from robot_command.program_interpreter import ProgramInterpreter
from robot_command.rpl import CommandInterpreter

if __name__ == '__main__':
    rospy.init_node('test_drive', anonymous=True)
    CommandInterpreter.status_report_cb = lambda _, cmd: print(cmd)
    interpreter = ProgramInterpreter()
    interpreter.load_program('./test_program3.py')
    interpreter.start_program()
    interpreter.wait_for_program_to_complete()

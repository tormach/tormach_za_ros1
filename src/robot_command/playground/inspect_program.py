#!/usr/bin/env python
from robot_command.robot_program import RobotProgram


if __name__ == '__main__':
    program = RobotProgram()
    program.read_from_file('./test_program3.py')
    print(str(program))
    for node in program.blocks:
        if node.type == 'movel':
            node.title = 'Test test hurrah'
            print(node.block.start_pos)
            print(node.block.end_pos)
    print(''.join(program.root_block.write()))

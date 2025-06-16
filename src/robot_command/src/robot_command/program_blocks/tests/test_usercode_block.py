import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, UserCodeBlock


@pytest.fixture
def sample_program():
    return '''\
def sample_program():
    print('hello world')
    '''


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


def test_newline_is_not_detected_as_usercode(program, sample_program):
    module = parso.parse(sample_program)
    root = RootBlock(module, program)

    program_suite = module.children[0].get_suite()
    result = [n for n in UserCodeBlock.read(program_suite.children[0], root)]

    assert len(result) == 0

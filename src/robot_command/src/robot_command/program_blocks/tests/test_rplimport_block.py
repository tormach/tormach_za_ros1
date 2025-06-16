import parso
import pytest

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks.rpl_block import INDENTATION_SPACES
from robot_command.program_blocks import (
    RootBlock,
    RPLImportBlock,
    UserCodeBlock,
)


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input',
    ['from robot_command.rpl import *\n'],
)
def test_rplimport_block_is_detected_correctly(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in RPLImportBlock.read(module.children[0], root)]
    assert len(result) == 1
    result = result[0]
    assert isinstance(result, RPLImportBlock)


@pytest.mark.parametrize(
    'test_input',
    [
        'from amongst import ugly\n',
        "import robot_command.rpl\n",
        'from robot_command.rpl import Foo, Bar\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in RPLImportBlock.read(module.children[0], root)]

    assert len(result) == 0


def test_rplimport_block_is_written_correctly(program):
    root = RootBlock(None, program)
    nested_block = UserCodeBlock(None, root)  # for testing indentation
    block = RPLImportBlock(None, nested_block)

    output = ''.join(block.write())

    assert (
        output == INDENTATION_SPACES * ' ' + 'from robot_command.rpl import *\n'
    )

import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks.rpl_block import INDENTATION_SPACES
from robot_command.program_blocks import RootBlock, PassBlock, UserCodeBlock


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


def test_pass_block_without_comment_is_detected_correctly(program):
    module = parso.parse('pass\n')
    root = RootBlock(module, program)

    result = [n for n in PassBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, PassBlock)


@pytest.mark.dependency()
def test_pass_block_with_comment_is_detected_correctly(program):
    module = parso.parse('pass  # TODO: implement\n')
    root = RootBlock(module, program)

    result = [n for n in PassBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, PassBlock)


@pytest.mark.dependency(
    depends=["test_pass_block_with_comment_is_detected_correctly"]
)
def test_read_pass_block_with_comment_is_written_correctly(program):
    module = parso.parse('pass  # tyrolean\n')
    root = RootBlock(module, program)
    block = [n for n in PassBlock.read(module.children[0], root)][0]

    output = ''.join(block.write())

    assert output == 'pass  # tyrolean\n'


def test_pass_block_is_written_correctly(program):
    root = RootBlock(None, program)
    nested_block = UserCodeBlock(None, root)  # for testing indentation
    block = PassBlock(None, nested_block)

    output = ''.join(block.write())

    assert output == INDENTATION_SPACES * ' ' + 'pass\n'

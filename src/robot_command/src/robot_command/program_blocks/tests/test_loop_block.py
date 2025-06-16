import pytest
import parso

from robot_command.program_blocks.loop_block import LoopType
from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    UserCodeBlock,
    LoopBlock,
    PassBlock,
)


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [('while True:\n  pass\n', 'True'), ('while x == 4:\n  pass\n', 'x == 4')],
)
def test_while_with_condition_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in LoopBlock.read(module.children[0], root)]

    assert len(result) == 1
    block = result[0]
    assert isinstance(block, LoopBlock)
    assert block.loop_type == LoopType.WhileLoop
    assert block.condition == expected
    assert len(block.children) == 1


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('for i in range(5):\n  pass\n', ['i', 5]),
        ('for y in range(737):\n  pass\n', ['y', 737]),
    ],
)
def test_for_with_range_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in LoopBlock.read(module.children[0], root)]

    assert len(result) == 1
    block = result[0]
    assert isinstance(block, LoopBlock)
    assert block.loop_type == LoopType.ForRangeLoop
    assert block.variable == expected[0]
    assert block.count == expected[1]
    assert len(block.children) == 1


@pytest.mark.parametrize(
    'test_input',
    [
        'while :\n    pass\n',
        'for x in [1, 2, 3]:\n    pass\n',
        'for a in something():\n    pass\n',
        'for i in range(1, 2):\n    pass\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in LoopBlock.read(module.children[0], root)]

    assert len(result) == 0


def test_while_block_is_written_correctly(program):
    root = RootBlock(None, program)
    block = LoopBlock(
        None, root, condition='z == 366', loop_type=LoopType.WhileLoop
    )
    block.add_child(PassBlock(None, block))

    output = ''.join(block.write())

    assert output == 'while z == 366:\n    pass\n'


def test_for_loop_is_written_correctly(program):
    root = RootBlock(None, program)
    block = LoopBlock(
        None, root, variable='y', count=707, loop_type=LoopType.ForRangeLoop
    )
    block.add_child(PassBlock(None, block))

    output = ''.join(block.write())

    assert output == 'for y in range(707):\n    pass\n'


def test_for_loop_is_written_correctly_when_count_is_set_as_double(program):
    root = RootBlock(None, program)
    block = LoopBlock(
        None, root, variable='z', count=721.0, loop_type=LoopType.ForRangeLoop
    )
    block.add_child(PassBlock(None, block))

    output = ''.join(block.write())

    assert output == 'for z in range(721):\n    pass\n'

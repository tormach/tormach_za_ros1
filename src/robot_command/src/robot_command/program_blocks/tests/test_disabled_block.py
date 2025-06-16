import itertools

import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    UserCodeBlock,
    DisabledBlock,
    PassBlock,
    IfBlock,
)


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(PassBlock, IfBlock, UserCodeBlock))


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('if False:\n  pass\n', (1, PassBlock)),
        ('if False:\n  if True:\n    pass\n  else:\n    pass\n', (2, IfBlock)),
    ],
)
def test_if_with_false_condition_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in DisabledBlock.read(module.children[0], root)]

    assert len(result) == expected[0]
    assert isinstance(result[0], expected[1])
    assert result[0].disabled is True
    assert result[0].parent is root


@pytest.mark.parametrize(
    'test_input',
    ['if False:\n  pass\nelse:\n  pass\n', 'if False:\n  pass\n  pass\n'],
)
def test_other_if_blocks_are_not_detected_as_disabled_block(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in DisabledBlock.read(module.children[0], root)]

    assert len(result) == 0


def test_disabled_block_is_written_correctly(program):
    root = RootBlock(None, program)
    block = PassBlock(None, root)
    block.disabled = True

    output = ''.join(block.write())

    assert output == 'if False:\n    pass\n'


def test_indentation_of_nested_disabled_block_is_correct(program):
    root = RootBlock(None, program)
    block1 = PassBlock(None, root)
    block1.disabled = True
    block2 = PassBlock(None, block1)
    block2.disabled = True

    output = ''.join(itertools.chain(block1.write(), block2.write()))

    assert (
        output == 'if False:\n    pass\n        if False:\n            pass\n'
    )


def test_disabled_group_block_is_written_in_one_if_false(program):
    root = RootBlock(None, program)
    block1 = PassBlock(None, root)
    block2 = PassBlock(None, root)
    block1.add_to_group(block2)
    block1.disabled = True

    output = ''.join(itertools.chain(block1.write(), block2.write()))

    assert output == 'if False:\n    pass\n    pass\n'


def test_disabled_group_block_is_written_in_if_multiple_are_false(program):
    root = RootBlock(None, program)
    block1 = PassBlock(None, root)
    block2 = PassBlock(None, root)
    block1.add_to_group(block2)
    block1.disabled = True
    block2.disabled = True

    output = ''.join(itertools.chain(block1.write(), block2.write()))

    assert output == 'if False:\n    pass\n    pass\n'

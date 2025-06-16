import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    UserCodeBlock,
    IfBlock,
    PassBlock,
)


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('if True:\n  pass\n', (1, ['True'], [1], ['if'])),
        ('if x == 4:\n  pass\n', (1, ['x == 4'], [1], ['if'])),
        (
            'if False:\n  pass\nelif True:\n  pass',
            (2, ['False', 'True'], [1, 1], ['if', 'elif']),
        ),
        (
            'if x == 4:\n  pass\nelse:\n  pass',
            (2, ['x == 4', ''], [1, 1], ['if', 'else']),
        ),
    ],
)
def test_if_with_condition_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in IfBlock.read(module.children[0], root)]

    assert len(result) == expected[0]
    for i, string in enumerate(expected[1]):
        block = result[i]
        assert isinstance(block, IfBlock)
        assert block.condition == string
        assert len(block.children) == expected[2][i]
        assert block.type == expected[3][i]


def test_if_with_condition_is_added_to_group(program):
    test_input = 'if True:\n  pass\nelif False:\n  pass\nelse:\n  pass'
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in IfBlock.read(module.children[0], root)]

    assert len(result) == 3
    assert result[0].in_group
    assert result[0].group_head == result[0]
    assert result[1].in_group
    assert result[1].group_head == result[0]
    assert result[2].in_group
    assert result[2].group_head == result[0]
    assert result[2].group_fixed


def test_if_and_elif_in_group_with_else_have_has_else_property_set(program):
    root = RootBlock(None, program)
    if_block = IfBlock(None, root, condition='True', type_='if')
    elif_block = IfBlock(None, root, condition='False', type_='elif')
    else_block = IfBlock(None, root, type_='else')
    if_block.add_to_group(elif_block)
    if_block.add_to_group(else_block)

    assert if_block.has_else
    assert elif_block.has_else
    assert else_block.has_else


def test_if_and_elif_in_group_without_else_dont_have_has_else_property_set(
    program,
):
    root = RootBlock(None, program)
    if_block = IfBlock(None, root, condition='True', type_='if')
    elif_block = IfBlock(None, root, condition='False', type_='elif')
    if_block.add_to_group(elif_block)

    assert not if_block.has_else
    assert not elif_block.has_else


def test_if_block_is_written_correctly(program):
    root = RootBlock(None, program)
    block = IfBlock(None, root, condition='True', type_='if')
    block.add_child(PassBlock(None, block))

    output = ''.join(block.write())

    assert output == 'if True:\n    pass\n'


def test_else_block_is_written_correctly(program):
    root = RootBlock(None, program)
    block = IfBlock(None, root, type_='else')
    block.add_child(PassBlock(None, block))

    output = ''.join(block.write())

    assert output == 'else:\n    pass\n'

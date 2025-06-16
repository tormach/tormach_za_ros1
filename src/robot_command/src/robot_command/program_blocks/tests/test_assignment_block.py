import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    UserCodeBlock,
    AssignmentBlock,
)


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('paguroid = 530.63\n', ('paguroid', '=', '530.63')),
        ('suomi = x * y\n', ('suomi', '=', 'x * y')),
        ('subverse += 3\n', ('subverse', '+=', '3')),
    ],
)
def test_assignment_with_expression_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in AssignmentBlock.read(module.children[0], root)]

    assert len(result) == 1
    node = result[0]
    assert node.name == expected[0]
    assert node.operator == expected[1]
    assert node.expression == expected[2]


@pytest.mark.parametrize(
    'test_input', ['print("hello world")\n', 'pose.x = 1.0\n']
)
def test_other_command_is_not_mistaken_as_assignment(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in AssignmentBlock.read(module.children[0], root)]

    assert len(result) == 0


def test_assignment_node_is_written_correctly(program):
    root = RootBlock(None, program)
    node = AssignmentBlock(
        None, root, name='siloist', operator='/=', expression='5 * sawer'
    )

    output = '\n'.join(node.write())

    assert output == 'siloist /= 5 * sawer\n'

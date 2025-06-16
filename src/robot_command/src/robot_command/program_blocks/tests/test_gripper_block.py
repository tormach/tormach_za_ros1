import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, GripperBlock, UserCodeBlock


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('actuate_gripper(0.0)\n', (0.0, 0.2, True)),
        ('actuate_gripper(position=0.4)\n', (0.4, 0.2, True)),
        ('actuate_gripper(0.5, effort=0.8)\n', (0.5, 0.8, True)),
        ('actuate_gripper(0.13, wait=False)\n', (0.13, 0.2, False)),
    ],
)
def test_gripper_block_is_parsed_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(GripperBlock.read(module.children[0], root))

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, GripperBlock)
    assert result.position == pytest.approx(expected[0])
    assert result.effort == pytest.approx(expected[1])
    assert result.wait is expected[2]


@pytest.mark.parametrize(
    'test_input',
    [
        'actuate_gripper("foo")\n',
        'actuate_gripper(effort=0.3)\n',
        'some_other_command()\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):  # sourcery skip: simplify-len-comparison
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(GripperBlock.read(module.children[0], root))

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ((0.0, 0.2, True), 'actuate_gripper(0.0)\n'),
    ],
)
def test_actuate_gripper_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = GripperBlock(
        None,
        root,
        position=test_input[0],
        effort=test_input[1],
        wait=test_input[2],
    )

    output = ''.join(block.write())

    assert output == expected

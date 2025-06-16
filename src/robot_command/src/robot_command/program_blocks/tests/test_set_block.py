import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, SetBlock, UserCodeBlock
from robot_command.program_blocks.set_block import SetType


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('set_digital_out(1, True)\n', (1, '', True)),
        ('set_digital_out(4, False)  \n', (4, '', False)),
        ('set_digital_out("brookite", True)\n', (0, 'brookite', True)),
        ('set_digital_out(\'eastre\', False)\n', (0, 'eastre', False)),
        ('set_digital_out("undid", False)  \n', (0, 'undid', False)),
        (
            "set_digital_out(nr_or_name=\"sorptive\", state=True)\n",
            (0, 'sorptive', True),
        ),
    ],
)
def test_set_digital_out_with_nr_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in SetBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, SetBlock)
    assert result.set_type == SetType.SetDigitalOut
    assert result.digital_out_nr == expected[0]
    assert result.digital_out_name == expected[1]
    assert result.digital_out_state == expected[2]


@pytest.mark.parametrize(
    'test_input',
    [
        'get_digital_in(1)\n',
        'some_other_command()\n',
        'set_digital_out()\n',
        'set_digital_out(10)\n',
        'set_digital_out(1, "foo")\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in SetBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ((889, '', True), 'set_digital_out(889, True)\n'),
        ((212, '', False), 'set_digital_out(212, False)\n'),
        ((0, 'steepled', True), 'set_digital_out("steepled", True)\n'),
        ((0, 'taction', False), 'set_digital_out("taction", False)\n'),
    ],
)
def test_set_digital_out_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = SetBlock(
        None,
        root,
        digital_out_nr=test_input[0],
        digital_out_name=test_input[1],
        digital_out_state=test_input[2],
    )

    block.set_type = SetType.SetDigitalOut
    output = ''.join(block.write())

    assert output == expected

import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    PathPilotBlock,
    UserCodeBlock,
)
from robot_command.program_blocks.pathpilot_block import CommandType


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('pathpilot_mdi("GO X0Y0")\n', ('GO X0Y0', '')),
        ('pathpilot_mdi(\'M100 P10\')  \n', ('M100 P10', '')),
        ('pathpilot_mdi("G1 Z10", "lessn")\n', ('G1 Z10', 'lessn')),
        (
            'pathpilot_mdi(command="M100", instance="purline")\n',
            ('M100', 'purline'),
        ),
    ],
)
def test_pathpilot_mdi_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in PathPilotBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, PathPilotBlock)
    assert result.command_type == CommandType.MdiCommand
    assert result.command_line == expected[0]
    assert result.instance == expected[1]


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('pathpilot_cycle_start()\n', ''),
        ('pathpilot_cycle_start("3YU")\n', '3YU'),
        ('pathpilot_cycle_start(instance="enacted")  \n', 'enacted'),
    ],
)
def test_pathpilot_cycle_start_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in PathPilotBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, PathPilotBlock)
    assert result.command_type == CommandType.CycleStartCommand
    assert result.instance == expected


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('pathpilot_abort()\n', ''),
        ('pathpilot_abort("3YU")\n', '3YU'),
        ('pathpilot_abort(instance="enacted")  \n', 'enacted'),
    ],
)
def test_pathpilot_abort_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in PathPilotBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, PathPilotBlock)
    assert result.command_type == CommandType.AbortCommand
    assert result.instance == expected


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('while get_pathpilot_state() != "ready":\n  sync()\n', ("", "ready")),
        (
            'while get_pathpilot_state("suggest") != "idle":\n  sync()\n',
            ("suggest", "idle"),
        ),
        (
            'while get_pathpilot_state(instance="separate") != "disconnected":\n  sync()\n',
            ("separate", "disconnected"),
        ),
    ],
)
def test_while_with_get_pathpilot_state_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in PathPilotBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, PathPilotBlock)
    assert result.command_type == CommandType.WaitForState
    assert result.instance == expected[0]
    assert result._state == expected[1]


@pytest.mark.parametrize(
    'test_input',
    [
        'pathpilot_mdi(1)\n',
        'some_other_command()\n',
        'pathpilot_mdi()\n',
        'pathpilot_mdi("G1 X10", 23)\n',
        'pathpilot_mdi("M20", bla="uberous")\n',
        'while get_pathpilot_state() is True:\n  sync()\n',
        'while get_pathpilot_state("remember") != "ready":\n  pass\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in PathPilotBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (('G1 Z20.1', ''), 'pathpilot_mdi("G1 Z20.1")\n'),
        (('T1 M6', ''), 'pathpilot_mdi("T1 M6")\n'),
        (('M100', 'consular'), 'pathpilot_mdi("M100", instance="consular")\n'),
    ],
)
def test_pathpilot_mdi_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = PathPilotBlock(
        None, root, command_line=test_input[0], instance=test_input[1]
    )

    block.command_type = CommandType.MdiCommand
    output = ''.join(block.write())

    assert output == expected


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('', 'pathpilot_cycle_start()\n'),
        ('costeen', 'pathpilot_cycle_start(instance="costeen")\n'),
    ],
)
def test_pathpilot_cycle_start_is_written_correctly(
    program, test_input, expected
):
    root = RootBlock(None, program)
    block = PathPilotBlock(None, root, instance=test_input)

    block.command_type = CommandType.CycleStartCommand
    output = ''.join(block.write())

    assert output == expected


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('', 'pathpilot_abort()\n'),
        ('costeen', 'pathpilot_abort(instance="costeen")\n'),
    ],
)
def test_pathpilot_abort_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = PathPilotBlock(None, root, instance=test_input)

    block.command_type = CommandType.AbortCommand
    output = ''.join(block.write())

    assert output == expected


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            ('ready', ''),
            'while get_pathpilot_state() != "ready":\n    sync()\n',
        ),
        (
            ('idle', 'claim'),
            'while get_pathpilot_state(instance="claim") != "idle":\n    sync()\n',
        ),
    ],
)
def test_get_pathpilot_state_is_written_correctly(
    program, test_input, expected
):
    root = RootBlock(None, program)
    block = PathPilotBlock(
        None, root, state=test_input[0], instance=test_input[1]
    )

    block.command_type = CommandType.WaitForState
    output = ''.join(block.write())

    assert output == expected

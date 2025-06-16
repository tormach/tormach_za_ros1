import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, MoveBlock, UserCodeBlock


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input',
    [
        'movel(p[1.0, 2, 3.0, 4, 5.0, 6])\n',
        'movej(j[1.0, 2, 3.0, 4, 5.0, 6])\n',
        'movel(p[-0.19, -0.17, 1.05, 0.5, 0.01, 0.01])\n',
        'movef(j[424.22, 85.37, 599.55, 192.41, 82.53, 716.73])\n',
    ],
)
def test_move_blocks_with_waypoint_values_are_not_detected_as_move_blocks(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert not result


@pytest.mark.parametrize(
    'test_input',
    [
        'movel(p[0, 2, 3.0, pi, -pi, pi / 2.0])\n',
        'movej(j[1.0, 2, 3.0, -pi, 5.0, 6])\n',
        'movel(p[-0.19, -0.17, 1.05, 0.5,pi / 2.0, 0.01])\n',
        'movef(j[300.40, 795.51, 84.12, 785.56, 88.78, 339.75])\n',
    ],
)
def test_move_blocks_with_non_number_values_are_not_detected(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert not result


def test_other_command_is_not_mistaken_as_movel(program):
    module = parso.parse('print("hello world")\n')
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert not result


def test_movel_command_with_variable_as_argument_is_parsed_correctly(program):
    module = parso.parse('movel(waypoint_1)\n')
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, MoveBlock)
    assert result.waypoint == 'waypoint_1'


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            ('movel', 'waypoint_1', dict(velocity=0.5)),
            'movel(waypoint_1, velocity=0.5)\n',
        ),
        (
            ('movej', 'waypoint_32', dict(velocity_scale=0.34)),
            'movej(waypoint_32, velocity_scale=0.34)\n',
        ),
        (('movef', '"youth"', {}), 'movef("youth")\n'),
    ],
)
def test_move_blocks_are_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = MoveBlock(None, root, type_=test_input[0])

    block.waypoint = test_input[1]
    for k, v in test_input[2].items():
        setattr(block, k, v)
    output = ''.join(block.write())

    assert output == expected


def test_movel_command_with_named_target_is_parsed_correctly(program):
    module = parso.parse('movel("grot")\n')
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, MoveBlock)
    assert result.waypoint == '"grot"'


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            'movel(director, accel_scale=0.929)\n',
            dict(acceleration_scale=0.929),
        ),
        ('movel(corner, velocity=200)\n', dict(velocity=200)),
        # ('movel(mistake, velocity=500*units.m/units.s)\n', (500, 0.5)),
        ('movel(save, accel=0.959)\n', dict(acceleration=0.959)),
        (
            'movel("hat", accel_scale=0.40, strict_limits=True)\n',
            dict(acceleration_scale=0.4, strict_limits=True),
        ),
        (
            'movel("rich", duration=5.0, probe=1)\n',
            dict(duration=5.0, probe_mode=1),
        ),
    ],
)
def test_movel_command_with_arguments_is_parsed_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, MoveBlock)
    for k, v in expected.items():
        assert getattr(result, k) == pytest.approx(v)


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('movej(director, velocity_scale=0.931)\n', (0.931, 0)),
        ('movej("critic", probe=3)\n', (1.0, 3)),
    ],
)
def test_movej_with_velocity_argument_is_parsed_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, MoveBlock)
    assert result.velocity_scale == pytest.approx(expected[0])
    assert result.probe_mode == pytest.approx(expected[1])


@pytest.mark.parametrize(
    'test_input',
    [
        'movef(pause, a=0.998)\n',
        'movef(pause, v=0.089, a=0.123)\n',
        'movef("account", a=0.388)\n',
    ],
)
def test_movej_and_movef_with_arguments_are_rejected(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(MoveBlock.read(module.children[0], root))

    assert not result

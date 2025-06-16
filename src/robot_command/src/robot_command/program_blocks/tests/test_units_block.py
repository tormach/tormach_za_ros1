import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, UnitsBlock, UserCodeBlock


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('set_units("mm")\n', ("mm", '', '')),
        ('set_units(linear="in")\n', ("in", '', '')),
        ('set_units("m", "rad")\n', ('m', 'rad', '')),
        ('set_units(None, "rad")\n', ('', 'rad', '')),
        ('set_units(ureg.m)\n', ('m', '', '')),
        ('set_units(angular=ureg.rad)\n', ('', 'rad', '')),
        ('set_units("in", "deg", "s")\n', ('in', 'deg', 's')),
        ('set_units(time=ureg.min)\n', ('', '', 'min')),
        ('set_units()\n', ('', '', '')),
    ],
)
def test_set_units_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(UnitsBlock.read(module.children[0], root))
    assert len(result) == 1
    result = result[0]
    assert isinstance(result, UnitsBlock)
    assert result.linear_unit == expected[0]
    assert result.angular_unit == expected[1]
    assert result.time_unit == expected[2]


@pytest.mark.parametrize(
    'test_input',
    [
        'set_unties()\n',
        'set_units(20)\n',
        'set_units(angular=30)\n',
        'set_units(time=321)\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = list(UnitsBlock.read(module.children[0], root))

    assert not result


@pytest.mark.parametrize(
    'linear_unit, angular_unit, time_unit, expected',
    [
        ("mm", None, None, 'set_units(linear="mm")\n'),
        (None, "deg", None, 'set_units(angular="deg")\n'),
        (None, None, "s", 'set_units(time="s")\n'),
        ("in", "rad", None, 'set_units("in", "rad")\n'),
        ("in", "deg", "min", 'set_units("in", "deg", "min")\n'),
    ],
)
def test_units_block_is_written_correctly(
    program, linear_unit, angular_unit, time_unit, expected
):
    root = RootBlock(None, program)
    block = UnitsBlock(
        None,
        root,
        linear_unit=linear_unit,
        angular_unit=angular_unit,
        time_unit=time_unit,
    )

    output = ''.join(block.write())

    assert output == expected

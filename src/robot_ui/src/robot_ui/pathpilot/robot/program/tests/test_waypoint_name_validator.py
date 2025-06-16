import pytest
from PySide6.QtGui import QValidator

from robot_ui.pathpilot.robot.program import RobotProgram, WaypointNameValidator
from robot_command import Waypoint
from robot_command.rpl import Pose, Joints


@pytest.fixture
def program():
    """
    :return: robot program with waypoints
    """
    robot_program = RobotProgram()
    waypoints = [
        Waypoint(
            name='dihalo',
            target=Pose(-671.13, 990.88, 307.47, -627.03, 383, 779.51),
        ),
        Waypoint(
            name='waypoint_1',
            target=Joints(867.09, -686, 962.96, -353.06, 655, 612.53),
        ),
    ]
    robot_program.reset_data(waypoints=waypoints)
    return robot_program


@pytest.mark.parametrize('test_input', ['waypoint_1', '_foo', 'fendy'])
def test_validator_validates_correct_input(test_input):
    validator = WaypointNameValidator()

    input_pos = len(test_input) - 1
    state, input_, pos = validator.validateFull(test_input, input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


@pytest.mark.parametrize('test_input', ['24_bar', '#4442', '"ada"', 'foo bar'])
def test_validator_invalidates_incorrect_input(test_input):
    validator = WaypointNameValidator()

    input_pos = len(test_input) - 1
    state, input_, pos = validator.validateFull(test_input, input_pos)

    assert state == QValidator.Invalid
    assert pos == input_pos


def test_validator_invalidates_existing_waypoint_name(program):
    validator = WaypointNameValidator()
    validator.waypoints = program

    input_pos = 0
    state, input_, pos = validator.validateFull('dihalo', input_pos)

    assert state == QValidator.Invalid
    assert pos == input_pos


def test_validator_validates_existing_waypoint_name_when_ignored(program):
    validator = WaypointNameValidator()
    validator.waypoints = program
    validator.ignoredName = 'waypoint_1'

    input_pos = 0
    state, input_, pos = validator.validateFull('waypoint_1', input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


def test_validator_validates_input_when_waypoint_name_does_not_exist(program):
    validator = WaypointNameValidator()
    validator.waypoints = program

    input_pos = 0
    state, input_, pos = validator.validateFull('prolix3', input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


def test_validator_generates_default_name_when_no_waypoint_exists():
    validator = WaypointNameValidator()
    validator.defaultPrefix = 'waypoint_'

    name = validator.generateDefaultName()

    assert name == 'waypoint_1'


def test_validator_increases_number_when_waypoint_exists(program):
    validator = WaypointNameValidator()
    validator.waypoints = program
    validator.defaultPrefix = 'waypoint_'

    name = validator.generateDefaultName()

    assert name == 'waypoint_2'

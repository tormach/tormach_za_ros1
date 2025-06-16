import pytest
from PySide6.QtTest import QSignalSpy

from robot_ui.pathpilot.robot.program import RobotProgram
from robot_ui.pathpilot.robot.program.waypoint_data import WaypointData
from robot_command import Waypoint
from robot_command.waypoint import TargetType


@pytest.fixture
def waypoint_program():
    robot_program = RobotProgram()
    waypoints = [
        Waypoint(
            name='bunco',
            uuid='IcojveBY',
            target=[792.42, 928.32, 665.17, 575.85, 729.42, 167.10],
            target_type=TargetType.Pose,
        ),
        Waypoint(
            name='awarn',
            uuid='wlJk9v8b',
            target=[719.63, 136.23, 5.17, 278.59, 250.52, 794.19],
            target_type=TargetType.Joints,
        ),
        Waypoint(
            name='yechs',
            uuid='gbflprR',
            target=[887.85, 205.48, 338.45, 618.34, 763.63, 752.52],
            target_type=TargetType.Joints,
        ),
    ]
    robot_program.reset_data(waypoints=waypoints)

    return robot_program


def test_main_attributes_are_empty_when_node_uuid_is_invalid(waypoint_program):
    waypoint_data = WaypointData(source=waypoint_program)

    waypoint_data.uuid = ''

    assert waypoint_data.valid is False
    assert waypoint_data.name == ''
    assert waypoint_data.target == []
    assert waypoint_data.targetType == TargetType.Pose


def test_main_attributes_are_valid_when_node_index_is_valid(waypoint_program):
    waypoint_data = WaypointData()
    waypoint = waypoint_program.waypoints[0]
    waypoint_data.source = waypoint_program

    waypoint_data.uuid = waypoint.uuid

    assert waypoint_data.name == waypoint.name
    assert waypoint_data.target == waypoint.target
    assert waypoint_data.targetType == waypoint.target_type
    assert waypoint_data.valid is True


def test_data_changed_signal_is_emitted_when_waypoint_is_updated(
    waypoint_program, qtbot
):
    waypoint_data = WaypointData()
    waypoint = waypoint_program.waypoints[1]
    waypoint_data.uuid = waypoint.uuid
    waypoint_data.source = waypoint_program
    spy = QSignalSpy(waypoint_data.dataChanged)

    waypoint_program.update_waypoint(waypoint, 'name', 'sparges')

    spy.wait(100)
    assert spy.count() == 1


def test_data_changed_signal_is_emitted_when_waypoint_is_removed(
    waypoint_program, qtbot
):
    waypoint_data = WaypointData()
    waypoint = waypoint_program.waypoints[1]
    waypoint_data.uuid = waypoint.uuid
    waypoint_data.source = waypoint_program
    spy = QSignalSpy(waypoint_data.dataChanged)

    waypoint_program.remove_waypoint(waypoint)

    spy.wait(100)
    assert spy.count() == 1


def test_data_changed_signal_is_emitted_program_is_reset(
    waypoint_program, qtbot
):
    waypoint_data = WaypointData()
    waypoint = waypoint_program.waypoints[1]
    waypoint_data.uuid = waypoint.uuid
    waypoint_data.source = waypoint_program
    spy = QSignalSpy(waypoint_data.dataChanged)

    waypoint_program.reset_data(waypoints=[])

    spy.wait(100)
    assert spy.count() == 1

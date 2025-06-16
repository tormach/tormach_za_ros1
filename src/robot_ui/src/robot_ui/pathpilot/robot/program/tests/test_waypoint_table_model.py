import pytest
from PySide6.QtCore import QModelIndex
from PySide6.QtTest import QSignalSpy, QAbstractItemModelTester

from robot_ui.pathpilot.robot.program import (
    WaypointTableModel,
    RobotProgram,
    ProgramWarning,
)
from robot_command import Waypoint
from robot_command.waypoint import TargetType

WAIT_TIME_MS = 100


@pytest.fixture
def program():
    """
    :return: robot program with waypoints
    """
    robot_program = RobotProgram()
    waypoints = [
        Waypoint(
            name='grifting',
            target=[-671.13, 990.88, 307.47, -627.03, 383, 779.51],
            target_type=TargetType.Pose,
        ),
        Waypoint(
            name='serpette',
            target=[867.09, -686, 962.96, -353.06, 655, 612.53],
            target_type=TargetType.Joints,
        ),
    ]
    robot_program.reset_data(waypoints=waypoints)
    return robot_program


@pytest.mark.dependency()
def test_creating_model_from_robot_program_works(program):
    model = WaypointTableModel()
    model.source = program

    assert model.rowCount(QModelIndex()) == 2
    assert model.columnCount(QModelIndex()) == 15
    index = model.index(0, 0, QModelIndex())
    assert model.data(index, model.Roles.NameRole) == 'grifting'
    assert model.data(index, model.Roles.TargetTypeRole) == TargetType.Pose
    assert isinstance(model.data(index, model.Roles.TargetRole), list)
    assert model.data(index, model.Roles.FrameRole) == ''
    assert model.data(index, model.Roles.ModifiedRole) is False
    assert model.data(index, model.Roles.XRole) == pytest.approx(-671.13)
    assert model.data(index, model.Roles.YRole) == pytest.approx(990.88)
    assert model.data(index, model.Roles.ZRole) == pytest.approx(307.47)
    assert model.data(index, model.Roles.ARole) == pytest.approx(-627.03)
    assert model.data(index, model.Roles.BRole) == pytest.approx(383)
    assert model.data(index, model.Roles.CRole) == pytest.approx(779.51)


def test_mapping_uuid_to_index_works_correctly(program):
    model = WaypointTableModel()
    model.source = program

    index = model.index_for_uuid(program.waypoints[0].uuid)
    assert index.isValid()
    assert index == model.index(0, 0, QModelIndex())


def test_mapping_uuid_which_does_not_exist_returns_invalid_index(program):
    model = WaypointTableModel()
    model.source = program

    index = model.index_for_uuid('hmg')
    assert not index.isValid()


def test_model_is_informed_when_waypoint_is_created_in_robot_program(
    program, qtbot
):
    model = WaypointTableModel()
    model.source = program
    spy1 = QSignalSpy(model.rowsAboutToBeInserted)
    spy2 = QSignalSpy(model.rowsInserted)

    program.create_waypoint()

    spy1.wait(WAIT_TIME_MS)
    assert spy1.count() == 1
    assert spy2.count() == 1
    assert spy1.at(0)[1] == 2  # row 2
    assert spy1.at(0)[2] == 2  # row 2
    index = model.index(2, 0, QModelIndex())
    assert index.isValid()


def test_uuid_indizes_are_updated_when_waypoint_is_created_in_robot_program(
    program, qtbot
):
    model = WaypointTableModel()
    model.source = program

    new_waypoint = program.create_waypoint()

    index = model.index_for_uuid(new_waypoint.uuid)
    assert index.isValid()
    assert index.internalPointer() == new_waypoint


def test_model_is_informed_when_waypoint_is_removed_from_robot_program(
    program, qtbot
):
    model = WaypointTableModel()
    model.source = program
    spy1 = QSignalSpy(model.rowsAboutToBeRemoved)
    spy2 = QSignalSpy(model.rowsRemoved)

    waypoint = program.waypoints[0]
    program.remove_waypoint(waypoint)

    spy1.wait(WAIT_TIME_MS)
    assert spy1.count() == 1
    assert spy2.count() == 1
    assert spy1.at(0)[1] == 0  # row 0
    assert spy1.at(0)[2] == 0  # row 0
    index = model.index_for_uuid(program.waypoints[0].uuid)
    assert index.isValid()
    assert index.row() == 0


def test_indizes_are_updated_when_waypoint_is_removed_from_robot_program(
    program, qtbot
):
    model = WaypointTableModel()
    model.source = program

    waypoint = program.waypoints[0]
    program.remove_waypoint(waypoint)

    index = model.index_for_uuid(waypoint.uuid)
    assert not index.isValid()


def model_is_informed_when_robot_program_is_reset(program):
    model = WaypointTableModel()
    model.source = program
    spy = QSignalSpy(model.modelAboutToBeReset)

    program.reset_data(waypoints=[])

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 1


def test_model_is_informed_when_robot_program_data_changes(program):
    model = WaypointTableModel()
    model.source = program
    spy = QSignalSpy(model.dataChanged)

    waypoint = program.waypoints[1]
    program.update_waypoint(waypoint, 'name', 'jackie')

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 1
    start_index = model.index_for_uuid(waypoint.uuid)
    end_index = model.index(start_index.row(), model.columnCount() - 1)
    assert spy.at(0)[0] == start_index  # updated index
    assert spy.at(0)[1] == end_index  # updated index


def test_set_warnings_informs_about_warning_changes(program):
    model = WaypointTableModel()
    model.source = program
    spy = QSignalSpy(model.dataChanged)

    waypoint = program.waypoints[0]
    warnings = {
        waypoint.uuid: [
            ProgramWarning(
                type_=ProgramWarning.Types.ShadowsPythonKeyword, message="depth"
            )
        ]
    }
    model.warnings = warnings

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 1
    start_index = model.index_for_uuid(waypoint.uuid)
    end_index = model.index(start_index.row(), model.columnCount() - 1)
    assert spy.at(0)[0] == start_index  # updated index
    assert spy.at(0)[1] == end_index  # updated index
    warning = model.data(start_index, WaypointTableModel.Roles.WarningRole)[0]
    assert warning.type == ProgramWarning.Types.ShadowsPythonKeyword


@pytest.mark.dependency(
    depends=['test_creating_model_from_robot_program_works']
)
def test_waypoint_model_implementation(program):
    model = WaypointTableModel()
    model.source = program
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )

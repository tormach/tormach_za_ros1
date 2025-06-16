import pytest
from collections import namedtuple

from PySide6.QtCore import Qt
from PySide6.QtTest import QAbstractItemModelTester

from robot_ui.pathpilot.robot.program import ProgramCodeListModel, RobotProgram
from robot_command.program_blocks import RPLBlock, RootBlock
from robot_command.waypoint import Waypoint, TargetType


DummyBlock = namedtuple('DummyBlock', 'start_pos end_pos get_code')


@pytest.fixture
def program():
    """
    :return: A program tree
    """
    lines = [
        'from robot_command.rpl import *\n',
        'debugger = p[0, 0, 0, 0, 0, 0]\n',
        'papier = j[0, 0, 0, 0, 0, 0]\n',
        'def main():\n',
        '    # foo bar\n',
        '\n',
        '    move(waypoint1)\n',
        '    sleep(0.5)\n',
    ]
    robot_program = RobotProgram()
    root_block = RootBlock(
        DummyBlock((0, 0), (9, 0), lambda: ''.join(lines)), robot_program
    )
    baz_block = RPLBlock(
        DummyBlock((4, 0), (9, 0), lambda: ''.join(lines[3:8])),
        root_block,
        type_='baz',
    )
    root_block.add_child(baz_block, modify=False)
    baz_block.add_child(
        RPLBlock(
            DummyBlock((7, 0), (8, 0), lambda: lines[6]),
            baz_block,
            type_='boltrope',
        ),
        modify=False,
    )
    baz_block.add_child(
        RPLBlock(
            DummyBlock((8, 0), (9, 0), lambda: lines[7]),
            baz_block,
            type_='malto',
        ),
        modify=False,
    )
    waypoints = [
        Waypoint(
            name='debugger',
            target=[0, 0, 0, 0, 0, 0],
            target_type=TargetType.Pose,
        ),
        Waypoint(
            name='papier',
            target=[0, 0, 0, 0, 0, 0],
            target_type=TargetType.Joints,
        ),
    ]
    robot_program.reset_data(root_block=root_block, waypoints=waypoints)
    return robot_program


@pytest.mark.dependency()
def test_creating_model_from_robot_program_works(program):
    model = ProgramCodeListModel()
    model.program = program

    assert model.rowCount() == 9
    assert (
        model.data(model.index(0, 0), Qt.DisplayRole)
        == 'from robot_command.rpl import *'
    )
    assert (
        model.data(model.index(1, 0), Qt.DisplayRole)
        == 'debugger = p[0, 0, 0, 0, 0, 0]'
    )
    assert (
        model.data(model.index(2, 0), Qt.DisplayRole)
        == 'papier = j[0, 0, 0, 0, 0, 0]'
    )
    assert model.data(model.index(3, 0), Qt.DisplayRole) == 'def main():'
    assert model.data(model.index(4, 0), Qt.DisplayRole) == '    # foo bar'
    assert model.data(model.index(5, 0), Qt.DisplayRole) == ''
    assert (
        model.data(model.index(6, 0), Qt.DisplayRole) == '    move(waypoint1)'
    )
    assert model.data(model.index(7, 0), Qt.DisplayRole) == '    sleep(0.5)'
    assert model.data(model.index(8, 0), Qt.DisplayRole) == ''


@pytest.mark.dependency(
    depends=[
        'test_creating_model_from_robot_program_works',
    ]
)
def test_program_code_listmodel_is_qabstractlistmodel(program):
    model = ProgramCodeListModel()
    model.program = program
    QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )

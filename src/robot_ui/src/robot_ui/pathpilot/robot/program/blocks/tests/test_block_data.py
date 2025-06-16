import pytest
from PySide6.QtTest import QSignalSpy

from robot_ui.pathpilot.robot.program import RobotProgram
from robot_ui.pathpilot.robot.program.blocks import BlockData, MoveBlockData

from robot_command.testing.program_test_data import DummyBlock
from robot_command.program_blocks import RPLBlock, RootBlock, MoveBlock


@pytest.fixture
def robot_program():
    program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), program)
    root_block.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_block, type_='fordone'),
        modify=False,
    )
    root_block.add_child(
        RPLBlock(DummyBlock((3, 0), (20, 0)), root_block, type_='twenties'),
        modify=False,
    )
    program.reset_data(root_block=root_block)

    return program


def test_main_attributes_are_empty_when_block_uuid_is_invalid():
    block_data = BlockData()

    block_data.uuid = ''

    assert block_data.type == ''
    assert block_data.valid is False
    assert block_data.nextUuid == ''
    assert block_data.previousUuid == ''


def test_main_attributes_are_correct_when_uuid_is_valid(robot_program):
    block_data = BlockData()
    block_data.program = robot_program

    block = robot_program.root_block.children[0]
    block_data.uuid = block.uuid

    assert block_data.valid
    assert block_data.type == 'fordone'


def test_data_changed_signal_is_emitted_when_block_data_is_updated(
    robot_program, qtbot
):
    block_data = BlockData()
    block_data.program = robot_program
    block = robot_program.root_block.children[0]
    block_data.uuid = block.uuid
    spy = QSignalSpy(block_data.dataChanged)

    robot_program.update_block(block, 'node', 12)

    spy.wait(100)
    assert spy.count() == 1


def test_data_changed_signal_is_emitted_when_block_is_removed(
    robot_program, qtbot
):
    block_data = BlockData()
    block_data.program = robot_program
    block = robot_program.root_block.children[0]
    block_data.uuid = block.uuid
    spy = QSignalSpy(block_data.dataChanged)

    robot_program.remove_block(block)

    spy.wait(100)
    assert spy.count() == 1


def test_data_changed_signal_is_emitted_when_robot_program_is_reset(
    robot_program, qtbot
):
    block_data = BlockData()
    block_data.program = robot_program
    block = robot_program.root_block.children[1]
    block_data.uuid = block.uuid
    spy = QSignalSpy(block_data.dataChanged)

    robot_program.reset_data(root_block=robot_program.root_block)

    spy.wait(100)
    assert spy.count() == 1


def test_previous_and_next_uuid_are_updated_when_block_is_moved_in_model(
    robot_program, qtbot
):
    block_data = BlockData()
    block_data.program = robot_program
    block = robot_program.root_block.children[1]
    block_data.uuid = block.uuid
    spy1 = QSignalSpy(block_data.previousUuidChanged)
    spy2 = QSignalSpy(block_data.nextUuidChanged)

    other_block = robot_program.root_block.children[0]
    robot_program.move_block(block, other_block)

    spy1.wait(100)
    assert spy1.count() == 1
    assert spy2.count() == 1


@pytest.fixture
def robot_program_with_move_block():
    program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), program)
    root_block.add_child(
        MoveBlock(None, root_block, waypoint='feuding'), modify=False
    )
    root_block.add_child(
        RPLBlock(DummyBlock((3, 0), (20, 0)), root_block, type_='twenties'),
        modify=False,
    )
    program.reset_data(root_block=root_block)

    return program


def test_type_matches_when_uuid_is_valid_and_type_is_same(
    robot_program_with_move_block,
):
    robot_program = robot_program_with_move_block
    block_data = MoveBlockData()
    block_data.program = robot_program

    block = robot_program.root_block.children[0]
    block_data.uuid = block.uuid

    assert block_data.valid
    assert block_data.typeMatches


def test_type_does_not_match_when_uuid_is_valid_and_type_is_different(
    robot_program_with_move_block,
):
    robot_program = robot_program_with_move_block
    block_data = MoveBlockData()
    block_data.program = robot_program

    block = robot_program.root_block.children[1]
    block_data.uuid = block.uuid

    assert block_data.valid
    assert not block_data.typeMatches

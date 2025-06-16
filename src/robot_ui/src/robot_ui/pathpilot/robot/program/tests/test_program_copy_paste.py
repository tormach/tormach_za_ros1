from collections import namedtuple

import pytest
from PySide6.QtTest import QSignalSpy

from robot_command.program_blocks import RPLBlock, RootBlock
from robot_command.testing.program_test_data import DummyBlock
from robot_ui.pathpilot.robot.program import (
    RobotProgram,
    ProgramManipulator,
    ProgramCopyPaste,
)
from robot_ui.pathpilot.robot.program.program_copy_paste import CopyPasteCommand


@pytest.fixture
def simple_program():
    """
    :return: A program tree:
    root
      [0] fumbler
      [1] amurca
    """
    robot_program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), robot_program)
    root_block.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_block, type_='fumbler'),
        modify=False,
    )
    root_block.add_child(
        RPLBlock(DummyBlock((2, 0), (3, 0)), root_block, type_='amurca'),
        modify=False,
    )

    robot_program.reset_data(root_block=root_block)
    return robot_program


@pytest.fixture
def setup(simple_program):
    TestSetup = namedtuple('TestSetup', 'program  manipulator copy_paste')
    manipulator = ProgramManipulator()
    manipulator.sourceProgram = simple_program
    copy_paste = ProgramCopyPaste()
    copy_paste.manipulator = manipulator
    return TestSetup(
        program=simple_program, manipulator=manipulator, copy_paste=copy_paste
    )


@pytest.mark.dependency()
def test_copy_makes_paste_possible(setup, qtbot):
    block1 = setup.program.root_block.children[0]
    spy = QSignalSpy(setup.copy_paste.pastePossibleChanged)

    setup.copy_paste.copy(block1.uuid)

    assert setup.copy_paste.pastePossible is True
    assert spy.count() == 1


@pytest.mark.dependency()
def test_copy_updates_source_uuid_and_current_command(setup, qtbot):
    block1 = setup.program.root_block.children[0]
    command_spy = QSignalSpy(setup.copy_paste.currentCommandChanged)
    uuid_spy = QSignalSpy(setup.copy_paste.sourceUuidChanged)

    setup.copy_paste.copy(block1.uuid)

    assert setup.copy_paste.pastePossible is True
    assert command_spy.count() == 1
    assert uuid_spy.count() == 1
    assert setup.copy_paste.currentCommand == CopyPasteCommand.CopyCommand
    assert setup.copy_paste.sourceUuid == block1.uuid


def test_cut_makes_paste_possible(setup, qtbot):
    block1 = setup.program.root_block.children[0]
    spy = QSignalSpy(setup.copy_paste.pastePossibleChanged)

    setup.copy_paste.cut(block1.uuid)

    assert setup.copy_paste.pastePossible is True
    assert spy.count() == 1


@pytest.mark.dependency()
def test_cut_updates_source_uuid_and_current_command(setup, qtbot):
    block1 = setup.program.root_block.children[0]
    command_spy = QSignalSpy(setup.copy_paste.currentCommandChanged)
    uuid_spy = QSignalSpy(setup.copy_paste.sourceUuidChanged)

    setup.copy_paste.cut(block1.uuid)

    assert setup.copy_paste.pastePossible is True
    assert command_spy.count() == 1
    assert uuid_spy.count() == 1
    assert setup.copy_paste.currentCommand == CopyPasteCommand.CutCommand
    assert setup.copy_paste.sourceUuid == block1.uuid


def test_copy_paste_copies_block(setup):
    block1 = setup.program.root_block.children[0]
    block2 = setup.program.root_block.children[1]

    setup.copy_paste.copy(block1.uuid)
    new_uuid = setup.copy_paste.paste(block2.uuid, before=True)

    program = setup.manipulator.modifiedProgram
    assert len(program.root_block.children) == 3
    assert program.root_block.children[1].type == 'fumbler'
    assert program.root_block.children[1].uuid == new_uuid


def test_cut_paste_moves_block(setup):
    program = setup.manipulator.modifiedProgram
    block1 = program.root_block.children[0]
    block2 = program.root_block.children[1]

    setup.copy_paste.cut(block2.uuid)
    new_uuid = setup.copy_paste.paste(block1.uuid, before=True)

    assert len(program.root_block.children) == 2
    assert block1 is program.root_block.children[1]
    assert block2 is program.root_block.children[0]
    assert block2.uuid == new_uuid
    assert setup.copy_paste.pastePossible is False


@pytest.mark.dependency(
    depends=['test_cut_updates_source_uuid_and_current_command']
)
def test_cut_paste_resets_source_uuid_and_current_command(setup):
    program = setup.manipulator.modifiedProgram
    block1 = program.root_block.children[0]
    block2 = program.root_block.children[1]
    command_spy = QSignalSpy(setup.copy_paste.currentCommandChanged)
    uuid_spy = QSignalSpy(setup.copy_paste.sourceUuidChanged)

    setup.copy_paste.cut(block2.uuid)
    setup.copy_paste.paste(block1.uuid, before=True)

    assert command_spy.count() == 2
    assert uuid_spy.count() == 2
    assert setup.copy_paste.sourceUuid == ''
    assert setup.copy_paste.currentCommand == CopyPasteCommand.NoCommand


@pytest.mark.dependency(depends=['test_copy_makes_paste_possible'])
def test_reset_history_clears_paste_possible(setup, qtbot):
    block1 = setup.program.root_block.children[0]
    spy = QSignalSpy(setup.copy_paste.pastePossibleChanged)
    setup.copy_paste.copy(block1.uuid)

    setup.manipulator.resetHistory()

    assert setup.copy_paste.pastePossible is False
    assert spy.count() == 2


@pytest.mark.dependency(
    depends=['test_copy_updates_source_uuid_and_current_command']
)
def test_reset_history_updates_source_uuid_and_current_command(setup, qtbot):
    block1 = setup.program.root_block.children[0]
    command_spy = QSignalSpy(setup.copy_paste.currentCommandChanged)
    uuid_spy = QSignalSpy(setup.copy_paste.sourceUuidChanged)
    setup.copy_paste.copy(block1.uuid)

    setup.manipulator.resetHistory()

    assert command_spy.count() == 2
    assert uuid_spy.count() == 2
    assert setup.copy_paste.sourceUuid == ''
    assert setup.copy_paste.currentCommand == CopyPasteCommand.NoCommand

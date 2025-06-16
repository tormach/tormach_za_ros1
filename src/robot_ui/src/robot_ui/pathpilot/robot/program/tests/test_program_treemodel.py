import pytest

from PySide6.QtCore import QModelIndex
from PySide6.QtTest import QSignalSpy, QAbstractItemModelTester

from robot_ui.pathpilot.robot.program import (
    ProgramTreeModel,
    RobotProgram,
    ProgramWarning,
)
from robot_command.program_blocks import RPLBlock, RootBlock, MoveBlock
from robot_command.rpl import ProgramPosition

from robot_command.testing.program_test_data import DummyBlock, DummyProgram

WAIT_TIME_MS = 10


@pytest.fixture
def test_program():
    """
    :return: A program tree
    root
      [0] foo
      [1] bar
      [2] baz
        [0] boltrope
        [1] malto
    """
    robot_program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), robot_program)
    root_block.add_child(
        RPLBlock(DummyBlock((1, 0), (2, 0)), root_block, type_='foo'),
        modify=False,
    )
    root_block.add_child(
        RPLBlock(DummyBlock((2, 0), (3, 0)), root_block, type_='bar'),
        modify=False,
    )
    baz_block = RPLBlock(DummyBlock((4, 0), (20, 0)), root_block, type_='baz')
    root_block.add_child(baz_block, modify=False)
    baz_block.add_child(
        RPLBlock(DummyBlock((4, 0), (15, 0)), baz_block, type_='boltrope'),
        modify=False,
    )
    baz_block.add_child(
        RPLBlock(DummyBlock((16, 0), (20, 0)), baz_block, type_='malto'),
        modify=False,
    )
    robot_program.reset_data(root_block=root_block)
    return robot_program


@pytest.mark.dependency()
def test_creating_model_from_robot_program_works(test_program):
    model = ProgramTreeModel()
    model.program = test_program

    assert model.rowCount(QModelIndex()) == 3
    assert model.columnCount(QModelIndex()) == 1  # just one for treeview
    index = model.index(0, 0, QModelIndex())
    assert model.rowCount(index) == 0
    assert model.data(index, model.Roles.TypeRole) == 'foo'
    index = model.index(1, 0, QModelIndex())
    assert model.data(index, model.Roles.TypeRole) == 'bar'
    baz_index = model.index(2, 0, QModelIndex())
    assert model.data(baz_index, model.Roles.TypeRole) == 'baz'
    assert model.rowCount(baz_index) == 2
    index = model.index(0, 0, baz_index)
    assert model.data(index, model.Roles.TypeRole) == 'boltrope'
    index = model.index(1, 0, baz_index)
    assert model.data(index, model.Roles.TypeRole) == 'malto'


def test_mapping_uuid_to_index_works_correctly(test_program):
    model = ProgramTreeModel()
    model.program = test_program

    index = model.indexForUuid(test_program.root_block.children[0].uuid)
    assert index.isValid()
    assert index == model.index(0, 0, QModelIndex())
    index = model.indexForUuid(test_program.root_block.children[1].uuid)
    assert index.isValid()
    assert index == model.index(1, 0, QModelIndex())
    baz_index = model.indexForUuid(test_program.root_block.children[2].uuid)
    assert baz_index.isValid()
    index = model.indexForUuid(
        test_program.root_block.children[2].children[1].uuid
    )
    assert index.isValid()
    assert index == model.index(1, 0, baz_index)


def test_mapping_program_position_to_index_works_correctly(test_program):
    model = ProgramTreeModel()
    model.program = test_program

    index = model.index_for_position(ProgramPosition(linum=1, filename=''))
    assert index == model.index(0, 0, QModelIndex())
    index = model.index_for_position(ProgramPosition(linum=10, filename=''))
    baz_index = model.index(2, 0, QModelIndex())
    assert index == model.index(0, 0, baz_index)


def test_mapping_program_position_which_does_not_exist_returns_invalid_index(
    test_program,
):
    model = ProgramTreeModel()
    model.program = test_program

    index = model.index_for_position(ProgramPosition(linum=666, filename=''))
    assert not index.isValid()


def test_model_is_informed_when_block_is_created_in_robot_program(
    test_program, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy1 = QSignalSpy(model.rowsAboutToBeInserted)
    spy2 = QSignalSpy(model.rowsInserted)

    before_block = test_program.root_block.children[1]
    test_program.create_block(before_block, type_='movel', before=True)
    test_program.create_block(before_block, type_='movel', before=False)

    spy1.wait(WAIT_TIME_MS)
    assert spy1.count() == 2
    assert spy2.count() == 2
    assert spy1.at(0)[1] == 1  # row 1
    assert spy1.at(0)[2] == 1  # row 1
    index = model.index(1, 0, QModelIndex())
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'movel'
    assert spy1.at(1)[1] == 3  # row 3
    assert spy1.at(1)[2] == 3  # row 3
    index = model.index(3, 0, QModelIndex())
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'movel'


def test_uuid_indizes_are_updated_when_block_is_created_in_robot_program(
    test_program,
):
    model = ProgramTreeModel()
    model.program = test_program

    before_block = test_program.root_block.children[1]
    new_block = test_program.create_block(before_block, type_='movel')

    index = model.indexForUuid(new_block.uuid)
    assert index.isValid()
    assert index.internalPointer() == new_block
    index = model.indexForUuid(test_program.root_block.children[2].uuid)
    assert index.isValid()
    assert index.row() == 2


def test_model_is_informed_when_block_is_copied_in_robot_program(
    test_program, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy1 = QSignalSpy(model.rowsAboutToBeInserted)
    spy2 = QSignalSpy(model.rowsInserted)

    target_block = test_program.root_block.children[1]
    source_block = test_program.root_block.children[0]
    test_program.copy_block(source_block, target_block, before=True)
    test_program.copy_block(source_block, target_block, before=False)

    spy1.wait(WAIT_TIME_MS)
    assert spy1.count() == 2
    assert spy2.count() == 2
    assert spy1.at(0)[1] == 1  # row 1
    assert spy1.at(0)[2] == 1  # row 1
    index = model.index(1, 0, QModelIndex())
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'foo'
    assert spy1.at(1)[1] == 3  # row 3
    assert spy1.at(1)[2] == 3  # row 3
    index = model.index(3, 0, QModelIndex())
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'foo'


def test_uuid_indizes_are_updated_when_block_is_copied_in_robot_program(
    test_program,
):
    model = ProgramTreeModel()
    model.program = test_program

    before_block = test_program.root_block.children[1]
    source_block = test_program.root_block.children[0]
    new_block = test_program.copy_block(source_block, before_block)

    index = model.indexForUuid(new_block.uuid)
    assert index.isValid()
    assert index.internalPointer() == new_block
    index = model.indexForUuid(test_program.root_block.children[2].uuid)
    assert index.isValid()
    assert index.row() == 2


def test_model_is_informed_when_child_block_is_created_in_robot_program(
    test_program, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy1 = QSignalSpy(model.rowsAboutToBeInserted)
    spy2 = QSignalSpy(model.rowsInserted)

    parent_block = test_program.root_block.children[1]
    test_program.create_child_block(parent_block, type_='pass')

    assert spy1.count() == 1
    assert spy2.count() == 1
    assert spy1.at(0)[1] == 0  # row 0
    assert spy1.at(0)[2] == 0  # row 0
    index = model.index(1, 0, QModelIndex())
    index = model.index(0, 0, index)
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'pass'


def test_model_is_informed_when_block_is_removed_from_robot_program(
    test_program, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy1 = QSignalSpy(model.rowsAboutToBeRemoved)
    spy2 = QSignalSpy(model.rowsRemoved)

    block = test_program.root_block.children[1]
    test_program.remove_block(block)

    spy1.wait(WAIT_TIME_MS)
    assert spy1.count() == 1
    assert spy2.count() == 1
    assert spy1.at(0)[1] == 1  # row 1
    assert spy1.at(0)[2] == 1  # row 1
    index = model.index(1, 0, QModelIndex())
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'baz'


def test_uuid_indizes_are_updated_when_block_is_removed_from_robot_program(
    test_program,
):
    model = ProgramTreeModel()
    model.program = test_program

    block = test_program.root_block.children[1]
    test_program.remove_block(block)

    index = model.indexForUuid(block.uuid)
    assert not index.isValid()
    index = model.indexForUuid(test_program.root_block.children[1].uuid)
    assert index.isValid()
    assert index.row() == 1


def test_program_position_is_removed_when_block_is_removed_from_robot_program(
    test_program,
):
    model = ProgramTreeModel()
    model.program = test_program

    block = test_program.root_block.children[0]
    test_program.remove_block(block)

    index = model.index_for_position(ProgramPosition(linum=1, filename=''))
    assert not index.isValid()


def test_model_is_informed_when_block_in_robot_program_is_moved(
    test_program, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy1 = QSignalSpy(model.rowsAboutToBeMoved)
    spy2 = QSignalSpy(model.rowsMoved)
    spy3 = QSignalSpy(model.dataChanged)

    block = test_program.root_block.children[1]
    target_block = test_program.root_block.children[0]
    test_program.move_block(block, target_block, before=True)
    test_program.move_block(block, target_block, before=False)

    spy2.wait(WAIT_TIME_MS)
    assert spy1.count() == 2
    assert spy2.count() == 2
    assert spy3.count() == 2
    assert spy1.at(0)[1] == 1  # row 1
    assert spy1.at(0)[2] == 1  # row 1 ->
    assert spy1.at(0)[4] == 0  # row 0
    assert spy1.at(1)[1] == 0  # row 0
    assert spy1.at(1)[2] == 0  # row 0 ->
    assert spy1.at(1)[4] == 2  # row 2


def test_indizes_are_updated_when_block_in_robot_program_is_moved(test_program):
    model = ProgramTreeModel()
    model.program = test_program

    block = test_program.root_block.children[1]
    before_block = test_program.root_block.children[0]
    test_program.move_block(block, before_block)

    index = model.indexForUuid(block.uuid)
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'bar'
    assert index.row() == 0
    index = model.indexForUuid(before_block.uuid)
    assert index.isValid()
    assert model.data(index, model.Roles.TypeRole) == 'foo'
    assert index.row() == 1


@pytest.fixture()
def empty_root_block():
    return RootBlock(DummyBlock((0, 0), (20, 0)), DummyProgram(path=''))


def test_model_is_informed_when_robot_program_is_reset(
    test_program, empty_root_block, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy = QSignalSpy(model.modelAboutToBeReset)

    test_program.reset_data(root_block=empty_root_block)

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 1


@pytest.fixture()
def program_with_move_block():
    """
    :return: A program tree
    root
      [0] movel
    """
    robot_program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (1, 0)), robot_program)
    root_block.add_child(
        MoveBlock(DummyBlock((1, 0), (2, 0)), root_block), modify=False
    )
    robot_program.reset_data(root_block=root_block)
    return robot_program


def test_model_is_informed_when_robot_program_data_changes(
    program_with_move_block, qtbot
):
    model = ProgramTreeModel()
    model.program = program_with_move_block
    spy = QSignalSpy(model.dataChanged)

    block = program_with_move_block.root_block.children[0]
    program_with_move_block.update_block(block, 'waypoint', 'unriddle')

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 1
    assert spy.at(0)[0] == model.indexForUuid(block.uuid)  # updated index
    assert spy.at(0)[1] == model.indexForUuid(block.uuid)  # updated index


def test_model_is_informed_about_children_changes_when_disabled_property_changes(
    test_program, qtbot
):
    model = ProgramTreeModel()
    model.program = test_program
    spy = QSignalSpy(model.dataChanged)

    block = test_program.root_block.children[2]
    block1 = test_program.root_block.children[2].children[0]
    block2 = test_program.root_block.children[2].children[1]
    test_program.update_block(block, 'disabled', True)

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 2
    assert spy.at(0)[0] == model.indexForUuid(block.uuid)  # updated index
    assert spy.at(0)[1] == model.indexForUuid(block.uuid)  # updated index
    assert spy.at(1)[0] == model.indexForUuid(block1.uuid)  # first index
    assert spy.at(1)[1] == model.indexForUuid(block2.uuid)  # last index


def test_set_warnings_informs_about_warning_changes(test_program, qtbot):
    model = ProgramTreeModel()
    model.program = test_program
    spy = QSignalSpy(model.dataChanged)

    block = test_program.root_block.children[1]
    warnings = {
        block.uuid: [
            ProgramWarning(
                type_=ProgramWarning.Types.MissingName, message="voice"
            )
        ]
    }
    model.warnings = warnings

    spy.wait(WAIT_TIME_MS)
    assert spy.count() == 1
    index = model.indexForUuid(block.uuid)
    assert spy.at(0)[0] == index  # updated index
    assert spy.at(0)[1] == index  # updated index
    warning = model.data(index, ProgramTreeModel.Roles.WarningRole)[0]
    assert warning.type == ProgramWarning.Types.MissingName


@pytest.mark.dependency(
    depends=['test_creating_model_from_robot_program_works']
)
def test_program_tree_model_implementation(test_program):
    model = ProgramTreeModel()
    model.program = test_program
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )

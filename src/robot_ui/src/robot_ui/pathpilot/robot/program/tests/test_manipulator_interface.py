import pytest
from unittest.mock import MagicMock
from PySide6.QtTest import QSignalSpy

from robot_ui.pathpilot.robot.program.manipulator_interface import (
    ManipulatorInterface,
    Command,
    GroupCommand,
)


class DummyCommand(Command):
    def execute(self, target):
        pass


class DummyManipulator(ManipulatorInterface):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = MagicMock()

    def apply_command(self):
        self._execute_command(DummyCommand())


@pytest.fixture
def manipulator():
    return DummyManipulator()


@pytest.mark.dependency()
def test_undo_undoes_the_last_modification(manipulator):
    manipulator.apply_command()
    manipulator.apply_command()

    manipulator.undo()

    assert len(manipulator._undo_history) == 1
    assert len(manipulator._redo_history) == 1


@pytest.mark.dependency(depends=['test_undo_undoes_the_last_modification'])
def test_redo_reverts_the_last_undo_operation(manipulator):
    manipulator.apply_command()
    manipulator.undo()

    manipulator.redo()

    assert len(manipulator._undo_history) == 1
    assert len(manipulator._redo_history) == 0


@pytest.mark.dependency(depends=['test_redo_reverts_the_last_undo_operation'])
def test_executing_a_command_clears_the_redo_history(manipulator):
    manipulator.apply_command()
    manipulator.undo()
    manipulator.redo()

    manipulator.apply_command()

    assert manipulator.undoPossible is True
    assert manipulator.redoPossible is False


def test_reset_history_clears_the_history(manipulator):
    manipulator.apply_command()
    manipulator.apply_command()

    manipulator.resetHistory()

    assert manipulator.undoPossible is False
    assert manipulator.redoPossible is False


@pytest.mark.dependency()
def test_undo_added_and_undo_possible_is_emit_when_command_is_added(
    manipulator,
):
    possible_spy = QSignalSpy(manipulator.undoPossibleChanged)
    added_spy = QSignalSpy(manipulator.undoAdded)

    manipulator.apply_command()

    assert possible_spy.count() == 1
    assert added_spy.count() == 1


@pytest.mark.dependency(
    depends=['test_undo_added_and_undo_possible_is_emit_when_command_is_added']
)
def test_undo_and_redo_signals_are_emitted_when_undo_is_executed(manipulator):
    manipulator.apply_command()
    undo_possible_spy = QSignalSpy(manipulator.undoPossibleChanged)
    redo_possible_spy = QSignalSpy(manipulator.redoPossibleChanged)
    undo_removed_spy = QSignalSpy(manipulator.undoRemoved)
    redo_added_spy = QSignalSpy(manipulator.redoAdded)

    manipulator.undo()

    assert undo_possible_spy.count() == 1
    assert redo_possible_spy.count() == 1
    assert undo_removed_spy.count() == 1
    assert redo_added_spy.count() == 1


@pytest.mark.dependency(
    depends=['test_undo_and_redo_signals_are_emitted_when_undo_is_executed']
)
def test_undo_and_redo_signals_are_emitted_when_redo_is_executed(manipulator):
    manipulator.apply_command()
    manipulator.undo()
    undo_possible_spy = QSignalSpy(manipulator.undoPossibleChanged)
    redo_possible_spy = QSignalSpy(manipulator.redoPossibleChanged)
    undo_added_spy = QSignalSpy(manipulator.undoAdded)
    redo_removed_spy = QSignalSpy(manipulator.redoRemoved)

    manipulator.redo()

    assert undo_possible_spy.count() == 1
    assert redo_possible_spy.count() == 1
    assert undo_added_spy.count() == 1
    assert redo_removed_spy.count() == 1


def test_removed_signals_are_emitted_when_reset_history_is_executed(
    manipulator,
):
    manipulator.apply_command()
    manipulator.apply_command()
    undo_cleared_spy = QSignalSpy(manipulator.undoCleared)
    redo_cleared_spy = QSignalSpy(manipulator.redoCleared)

    manipulator.resetHistory()

    assert undo_cleared_spy.count() == 1
    assert redo_cleared_spy.count() == 1


def test_commands_in_group_are_grouped_as_one_command(manipulator):
    manipulator.beginGroup()
    manipulator.apply_command()
    manipulator.apply_command()
    manipulator.endGroup()

    assert len(manipulator._undo_history) == 1
    assert isinstance(manipulator._undo_history[0], GroupCommand)


def test_undo_when_group_is_active_ends_group_first(manipulator):
    manipulator.beginGroup()
    manipulator.apply_command()
    manipulator.apply_command()

    manipulator.undo()

    assert len(manipulator._undo_history) == 0
    assert len(manipulator._redo_history) == 1
    assert isinstance(manipulator._redo_history[0], GroupCommand)


def test_redo_when_group_is_active_ends_group(manipulator):
    manipulator.beginGroup()
    manipulator.apply_command()
    manipulator.apply_command()

    manipulator.redo()

    assert len(manipulator._undo_history) == 1
    assert isinstance(manipulator._undo_history[0], GroupCommand)

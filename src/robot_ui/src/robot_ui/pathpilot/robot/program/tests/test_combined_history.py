from collections import namedtuple

import pytest

from robot_ui.pathpilot.robot.program.combined_history import CombinedHistory
from test_manipulator_interface import DummyManipulator
from PySide6.QtTest import QSignalSpy

WAIT_TIMEOUT_MS = 100


@pytest.fixture()
def s():
    Setup = namedtuple('Setup', 'manipulator1 manipulator2 history')
    manipulator1 = DummyManipulator()
    manipulator2 = DummyManipulator()
    history = CombinedHistory()
    history.manipulators = [manipulator1, manipulator2]

    return Setup(manipulator1, manipulator2, history)


@pytest.mark.dependency()
def test_commands_are_added_to_undo_history(s):
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()

    assert len(s.history._undo_history) == 3


@pytest.mark.dependency(depends=['test_commands_are_added_to_undo_history'])
def test_undo_commands_are_added_to_redo_history(s):
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()

    s.manipulator2.undo()

    assert len(s.history._undo_history) == 2
    assert len(s.history._redo_history) == 1


@pytest.mark.dependency(
    depends=['test_undo_commands_are_added_to_redo_history']
)
def test_redo_commands_are_added_to_the_undo_history(s):
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()
    s.manipulator2.undo()
    s.manipulator1.undo()

    s.manipulator2.redo()

    assert len(s.history._undo_history) == 2
    assert len(s.history._redo_history) == 1


def test_reset_history_removes_all_commands_from_sender_from_the_history(s):
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()

    s.manipulator1.resetHistory()

    assert len(s.history._undo_history) == 1


@pytest.mark.dependency()
def test_undo_is_applied_to_correct_sender(s):
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()

    s.history.undo()

    assert len(s.history._undo_history) == 2
    assert len(s.history._redo_history) == 1
    assert len(s.manipulator2._undo_history) == 1
    assert len(s.manipulator2._redo_history) == 1


@pytest.mark.dependency(depends=['test_undo_is_applied_to_correct_sender'])
def test_redo_is_applied_to_correct_sender(s):
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()
    s.history.undo()
    s.history.undo()

    s.history.redo()

    assert len(s.history._undo_history) == 2
    assert len(s.history._redo_history) == 1
    assert len(s.manipulator1._undo_history) == 1
    assert len(s.manipulator2._undo_history) == 1


@pytest.mark.dependency(depends=['test_undo_is_applied_to_correct_sender'])
def test_reset_history_resets_all_history_and_signals_undo_redo_possible(
    s, qtbot
):
    s.manipulator2.apply_command()
    s.manipulator1.apply_command()
    s.manipulator2.apply_command()
    s.history.undo()
    spy1 = QSignalSpy(s.history.undoPossibleChanged)
    spy2 = QSignalSpy(s.history.redoPossibleChanged)

    s.history.resetHistory()
    spy1.wait(WAIT_TIMEOUT_MS)
    spy2.wait(WAIT_TIMEOUT_MS)

    assert len(s.history._undo_history) == 0
    assert len(s.history._redo_history) == 0
    assert len(s.manipulator2._undo_history) == 0
    assert len(s.manipulator2._redo_history) == 0
    assert spy1.count() == 1
    assert spy2.count() == 1

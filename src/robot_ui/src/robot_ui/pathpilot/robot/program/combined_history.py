import contextlib

from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtQml import QmlElement

from .program_manipulator import Command

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CombinedHistory(QObject):
    """Combines the history of multiple manipulators into one."""

    manipulatorsChanged = Signal()
    redoPossibleChanged = Signal()
    undoPossibleChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._manipulators = []
        self._undo_history = []
        self._redo_history = []
        self._undo_sender_map = {}
        self._redo_sender_map = {}

    @Property(list, notify=manipulatorsChanged)
    def manipulators(self):
        return self._manipulators

    @manipulators.setter
    def manipulators(self, value):
        if value == self._manipulators:
            return

        old_manipulators = self._manipulators
        self._manipulators = value
        self.manipulatorsChanged.emit()

        self._reconnect_signals(old_manipulators, self._manipulators)

    @Property(bool, notify=undoPossibleChanged)
    def undoPossible(self):
        return any(self._undo_history)

    @Property(bool, notify=redoPossibleChanged)
    def redoPossible(self):
        return any(self._redo_history)

    @Slot()
    def resetHistory(self):
        self._undo_history = []
        self._redo_history = []
        self._undo_sender_map.clear()
        self._redo_sender_map.clear()
        for manipulator in self._manipulators:
            manipulator.resetHistory()
        self.undoPossibleChanged.emit()
        self.redoPossibleChanged.emit()

    @Slot()
    def undo(self):
        if not self._undo_history:
            return
        last_command = self._undo_history[-1]
        sender = self._undo_sender_map[last_command]
        sender.undo()

    @Slot()
    def redo(self):
        if not self._redo_history:
            return
        last_command = self._redo_history[-1]
        sender = self._redo_sender_map[last_command]
        sender.redo()

    @Slot(Command)
    def _on_undo_added(self, command):
        self._add_undo(command, self.sender())

    @Slot(Command)
    def _on_redo_added(self, command):
        self._add_redo(command, self.sender())

    @Slot(Command)
    def _on_undo_removed(self, command):
        if command not in self._undo_sender_map:
            return
        self._remove_undo(command)

    @Slot(Command)
    def _on_redo_removed(self, command):
        if command not in self._redo_sender_map:
            return
        self._remove_redo(command)

    @Slot()
    def _on_undo_cleared(self):
        sender = self.sender()
        for key in list(self._undo_sender_map.keys()):
            item = self._undo_sender_map[key]
            if item is not sender:
                continue
            self._remove_undo(key)

    @Slot()
    def _on_redo_cleared(self):
        sender = self.sender()
        for key in list(self._redo_sender_map.keys()):
            item = self._redo_sender_map[key]
            if item is not sender:
                continue
            self._remove_redo(key)

    def _reconnect_signals(self, old, new):
        to_remove = set(old)
        for item in new:
            if item in to_remove:
                to_remove.remove(item)
            if item in old:
                continue  # already connected
            if item is None:
                continue
            item.undoAdded.connect(self._on_undo_added)
            item.undoRemoved.connect(self._on_undo_removed)
            item.undoCleared.connect(self._on_undo_cleared)
            item.redoAdded.connect(self._on_redo_added)
            item.redoRemoved.connect(self._on_redo_removed)
            item.redoCleared.connect(self._on_redo_cleared)

        for item in to_remove:
            with contextlib.suppress(RuntimeError):
                item.undoAdded.disconnect(self._on_undo_added)
                item.undoRemoved.disconnect(self._on_undo_removed)
                item.undoCleared.disconnect(self._on_undo_cleared)
                item.redoAdded.disconnect(self._on_redo_added)
                item.redoRemoved.disconnect(self._on_redo_removed)
                item.redoCleared.disconnect(self._on_redo_cleared)

    def _add_undo(self, command, sender):
        self._undo_sender_map[command] = sender
        self._undo_history.append(command)
        self.undoPossibleChanged.emit()

    def _remove_undo(self, command):
        self._undo_sender_map.pop(command)
        self._undo_history.remove(command)
        self.undoPossibleChanged.emit()

    def _add_redo(self, command, sender):
        self._redo_sender_map[command] = sender
        self._redo_history.append(command)
        self.redoPossibleChanged.emit()

    def _remove_redo(self, command):
        self._redo_sender_map.pop(command)
        self._redo_history.remove(command)
        self.redoPossibleChanged.emit()

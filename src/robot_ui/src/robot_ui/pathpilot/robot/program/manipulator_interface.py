import rospy
from PySide6.QtCore import QObject, Signal, Property, Slot


class CommandError(Exception):
    pass


class Command:
    def execute(self, target):
        raise NotImplementedError()


class GroupCommand(Command):
    def __init__(self, commands=None):
        super().__init__()

        if commands is None:
            commands = []
        self.commands = commands

    def execute(self, target):
        for command in self.commands:
            command.execute(target)


class ManipulatorInterface(QObject):
    """Common interface for all manipulators with history."""

    undoPossibleChanged = Signal()
    redoPossibleChanged = Signal()

    undoAdded = Signal(Command)
    undoRemoved = Signal(Command)
    undoCleared = Signal()

    redoAdded = Signal(Command)
    redoRemoved = Signal(Command)
    redoCleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._undo_history = []
        self._redo_history = []
        self._source = None
        self._modified = None
        # support for grouping commands
        self._group = []
        self._group_active = False

    @Property(bool, notify=undoPossibleChanged)
    def undoPossible(self):
        return any(self._undo_history)

    @Property(bool, notify=redoPossibleChanged)
    def redoPossible(self):
        return any(self._redo_history)

    @Slot()
    def resetHistory(self):
        if not self._source:
            return
        self._source.copy_data_to(self._modified)

        self._clear_redo()
        self._clear_undo()

    @Slot()
    def undo(self):
        if not self._source:
            return
        if self._group_active:
            self.endGroup()
        if not any(self._undo_history):
            return
        self._source.copy_data_to(self._modified)

        self._add_redo(self._pop_undo())
        for command in self._undo_history:
            command.execute(self._modified)

    @Slot()
    def redo(self):
        if not self._source:
            return
        if self._group_active:
            self.endGroup()
        if not any(self._redo_history):
            return

        command = self._pop_redo()
        self._execute_command(command, delete_redo=False)

    @Slot()
    def beginGroup(self):
        self._group_active = True

    @Slot()
    def endGroup(self):
        if not self._group_active:
            return
        self._group_active = False
        if len(self._group) == 0:
            return

        command = GroupCommand(commands=self._group[:])
        self._group = []
        self._add_undo(command)

    def _execute_command(self, command, delete_redo=True):
        try:
            command.execute(self._modified)
        except CommandError as e:
            rospy.logwarn(str(e))
        else:
            if not self._group_active:
                self._add_undo(command)
            else:
                self._group.append(command)
            if delete_redo:
                self._clear_redo()

    def _add_undo(self, command):
        self._undo_history.append(command)
        self.undoAdded.emit(command)
        self.undoPossibleChanged.emit()

    def _pop_undo(self):
        command = self._undo_history.pop(-1)
        self.undoRemoved.emit(command)
        self.undoPossibleChanged.emit()
        return command

    def _clear_undo(self):
        del self._undo_history[:]
        self.undoCleared.emit()
        self.undoPossibleChanged.emit()

    def _add_redo(self, command):
        self._redo_history.append(command)
        self.redoAdded.emit(command)
        self.redoPossibleChanged.emit()

    def _pop_redo(self):
        command = self._redo_history.pop(-1)
        self.redoRemoved.emit(command)
        self.redoPossibleChanged.emit()
        return command

    def _clear_redo(self):
        del self._redo_history[:]
        self.redoCleared.emit()
        self.redoPossibleChanged.emit()

import contextlib
from enum import IntEnum, auto

from PySide6.QtCore import QObject, Signal, Property, Slot, QEnum
from PySide6.QtQml import QmlElement

from .program_manipulator import ProgramManipulator


class CopyPasteCommand(IntEnum):
    NoCommand = auto()
    CopyCommand = auto()
    CutCommand = auto()


QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramCopyPaste(QObject):
    """
    Implements copy and paste functionality for a robot program.
    """

    QEnum(CopyPasteCommand)

    manipulatorChanged = Signal(ProgramManipulator)
    pastePossibleChanged = Signal()
    currentCommandChanged = Signal()
    sourceUuidChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._manipulator = None
        self._node_command = CopyPasteCommand.NoCommand
        self._node_uuid = ''

    @Property(int, notify=currentCommandChanged)
    def currentCommand(self):
        return self._node_command

    @Property(str, notify=sourceUuidChanged)
    def sourceUuid(self):
        return self._node_uuid

    @Property(ProgramManipulator, notify=manipulatorChanged)
    def manipulator(self):
        return self._manipulator

    @manipulator.setter
    def manipulator(self, value):
        if value == self._manipulator:
            return
        old_value = self._manipulator
        self._manipulator = value
        self.manipulatorChanged.emit(value)

        if old_value:
            with contextlib.suppress(RuntimeError):
                old_value.undoCleared.disconnect(self._reset_command)
        if value:
            value.undoCleared.connect(self._reset_command)

    @Property(bool, notify=pastePossibleChanged)
    def pastePossible(self):
        return self._node_command != CopyPasteCommand.NoCommand

    @Slot(str)
    def copy(self, uuid):
        if not self._manipulator:
            return

        self._node_uuid = uuid
        self._node_command = CopyPasteCommand.CopyCommand
        self.pastePossibleChanged.emit()
        self.sourceUuidChanged.emit()
        self.currentCommandChanged.emit()

    @Slot(str)
    def cut(self, uuid):
        if not self._manipulator:
            return

        self._node_uuid = uuid
        self._node_command = CopyPasteCommand.CutCommand
        self.pastePossibleChanged.emit()
        self.sourceUuidChanged.emit()
        self.currentCommandChanged.emit()

    @Slot(str, result=str)
    def paste(self, uuid, before=False):
        if not self._manipulator:
            return ''

        if self._node_command == CopyPasteCommand.CopyCommand:
            uuid = self._manipulator.copyBlock(
                self._node_uuid, uuid, before=before
            )
        elif self._node_command == CopyPasteCommand.CutCommand:
            uuid = self._manipulator.moveBlock(
                self._node_uuid, uuid, before=before
            )
            self._reset_command()
        else:
            uuid = ''

        return uuid

    @Slot()
    def _reset_command(self):
        self._node_command = CopyPasteCommand.NoCommand
        self._node_uuid = ''
        self.pastePossibleChanged.emit()
        self.sourceUuidChanged.emit()
        self.currentCommandChanged.emit()

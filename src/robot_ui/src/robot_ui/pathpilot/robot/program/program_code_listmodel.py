import contextlib
from typing import List, Optional
from PySide6.QtCore import (
    QAbstractListModel,
    QObject,
    Signal,
    Property,
    Slot,
    Qt,
)
from PySide6.QtQml import QmlElement

from robot_command.rpl import ProgramPosition

from .robot_program import RobotProgram

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramCodeListModel(QAbstractListModel):
    programChanged = Signal()
    lineCountChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._program: Optional[RobotProgram] = None
        self._code_lines: List[str] = []

        self.programChanged.connect(self._on_program_reset)
        self.modelReset.connect(self.lineCountChanged)

    @Property(QObject, notify=programChanged)  # RobotProgram
    def program(self):
        return self._program

    @program.setter
    def program(self, new_program):
        if new_program == self._program:
            return
        old_program = self._program
        self._program = new_program
        self.programChanged.emit()

        if old_program:
            with contextlib.suppress(RuntimeError):
                old_program.reset.disconnect(self._on_program_reset)
        if new_program:
            new_program.reset.connect(self._on_program_reset)

    @Property(int, notify=lineCountChanged)
    def lineCount(self):
        return len(self._code_lines)

    @Slot()
    def _on_program_reset(self):
        self.beginResetModel()
        self._root_node = self._program.root_block if self._program else None
        self._update_code_lines()
        self.endResetModel()

    def _update_code_lines(self):
        self._code_lines = []
        if not self._root_node:
            return
        self._code_lines = self._root_node.code.split('\n')

    def rowCount(self, _parent=None):
        return self.lineCount

    def data(self, index, role):
        if not index.isValid():
            return None
        try:
            return (
                self._code_lines[index.row()]
                if role == Qt.DisplayRole
                else None
            )
        except IndexError:
            return None

    def index_for_position(self, position: ProgramPosition):
        return self.createIndex(position.linum, 0)

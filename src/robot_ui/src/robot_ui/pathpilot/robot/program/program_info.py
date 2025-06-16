import contextlib

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from robot_command.program_blocks import RPLBlockWalker, ProgramBlock

from .robot_program import RobotProgram

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramInfo(QObject):
    programChanged = Signal()
    nameChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._program: RobotProgram = None
        self._name = ''

        self.programChanged.connect(self._update_info)

    @Property(QObject, notify=programChanged)  # RobotProgram
    def program(self):
        return self._program

    @program.setter
    def program(self, value):
        if value == self._program:
            return
        old_value = self._program
        self._program = value
        self.programChanged.emit()

        if old_value:
            with contextlib.suppress(RuntimeError):
                old_value.reset.disconnect(self._update_info)
        if value:
            value.reset.connect(self._update_info)
        else:
            self._reset_info()

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    def _reset_info(self):
        self._name = ''
        self.nameChanged.emit(self._name)

    @Slot()
    def _update_info(self):
        for node in RPLBlockWalker(self._program.root_block):
            if isinstance(node, ProgramBlock) and node.type == 'mainprogram':
                self._name = node.name
                self.nameChanged.emit(self._name)

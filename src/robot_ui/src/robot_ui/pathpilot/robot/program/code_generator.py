import contextlib

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from .robot_program import RobotProgram

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CodeGenerator(QObject):
    robotProgramChanged = Signal()
    codeChanged = Signal()
    autoUpdateChanged = Signal(bool)

    def __init__(
        self,
        parent: QObject = None,
        robot_program: RobotProgram = None,
        auto_update: bool = False,
    ):
        super().__init__(parent)

        self._auto_update = auto_update
        self._code = ''
        self._robot_program = robot_program

        self.autoUpdateChanged.connect(self._connect_or_disconnect_update)
        self.robotProgramChanged.connect(self._connect_or_disconnect_update)

    @Property(RobotProgram, notify=robotProgramChanged)
    def robotProgram(self):
        return self._robot_program

    @robotProgram.setter
    def robotProgram(self, value):
        if value == self._robot_program:
            return
        self._robot_program = value
        self.robotProgramChanged.emit()

    @Property(str, notify=codeChanged)
    def code(self):
        return self._code

    @Property(bool, notify=autoUpdateChanged)
    def autoUpdate(self):
        return self._auto_update

    @autoUpdate.setter
    def autoUpdate(self, value):
        if value == self._auto_update:
            return
        self._auto_update = value
        self.autoUpdateChanged.emit(value)

    @Slot()
    def update(self):
        if not (self._robot_program and self._robot_program.root_block):
            return

        self._code = ''.join(self._robot_program.generate_code())
        self.codeChanged.emit()

    @Slot()
    def _connect_or_disconnect_update(self):
        if not self._robot_program:
            return

        if self._auto_update:
            self._robot_program.reset.connect(self.update)
            self.update()
        else:
            with contextlib.suppress(RuntimeError):
                self._robot_program.reset.disconnect(self.update)

import rospy
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from .robot_program import RobotProgram

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramWriter(QObject):
    """Writes a robot program to a file."""

    _program = None  # type: RobotProgram

    pathChanged = Signal(str)
    programWritten = Signal()
    programChanged = Signal()
    writingChanged = Signal(bool)

    def __init__(self, parent=None, path='', program=None):
        super().__init__(parent)

        self._path = path
        self._program: RobotProgram = program
        self._writing = False

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(QObject, notify=programChanged)  # RobotProgram
    def program(self):
        return self._program

    @program.setter
    def program(self, value):
        if value == self._program:
            return
        self._program = value
        self.programChanged.emit()

    @Property(bool, notify=writingChanged)
    def writing(self):
        return self._writing

    @Slot()
    def write(self):
        self._write()

    @Slot(str)
    def writeToPath(self, path):
        self._write(path)

    def _write(self, path=''):
        if not (self._program and self._program.root_block):
            return

        program_path = path if path else self._path

        try:
            self._writing = True
            self.writingChanged.emit(True)
            self._program.write_to_file(program_path)
        except OSError as e:
            rospy.logerr(f'writing to file {program_path} failed: {str(e)}')
        else:
            self.programWritten.emit()
        finally:
            self._writing = False
            self.writingChanged.emit(False)

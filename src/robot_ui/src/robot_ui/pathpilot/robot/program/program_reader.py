import traceback

import rospy
from PySide6.QtCore import Slot
from PySide6.QtCore import QObject, Signal, Property
from PySide6.QtQml import QmlElement

from .program_treemodel import ProgramTreeModel
from .robot_program import RobotProgram


QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramReader(QObject):
    """Loads a robot program from a file."""

    pathChanged = Signal(str)
    modelChanged = Signal(ProgramTreeModel)
    programChanged = Signal()
    validChanged = Signal(bool)

    def __init__(self, parent=None, path=''):
        super().__init__(parent)
        self._valid = False
        self._path = path
        self._program = RobotProgram()

        self.pathChanged.connect(self._update_program)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(bool, notify=validChanged)
    def valid(self):
        return self._valid

    @Property(RobotProgram, notify=programChanged)
    def program(self):
        return self._program

    @Slot()
    def update(self):
        self._update_program()

    @Slot()
    def _update_program(self):
        if self._path == '':
            self._program.clear()
            self._valid = False
        else:
            try:
                self._program.read_from_file(self._path)
            except Exception as e:
                self._program.clear()
                # error also reported from interpreter, log info only
                rospy.loginfo(f"Reading program failed: {str(e)}")
                traceback.print_exc()
                self._valid = False
            else:
                self._valid = True
                self.programChanged.emit()

        self.validChanged.emit(self._valid)

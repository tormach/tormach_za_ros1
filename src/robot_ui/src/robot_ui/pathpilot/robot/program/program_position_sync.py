from PySide6.QtCore import (
    Property,
    Signal,
    Slot,
    QObject,
    QItemSelectionModel,
)
from PySide6.QtQml import QmlElement

import rospy
from robot_command_msgs import msg

from robot_command.rpl import ProgramPosition

from ...qt_helpers import ensure_cleanup

PROGRAM_POSITION_TOPIC = '/robot_command/program_position'

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramPositionSync(QObject):
    programModelChanged = Signal()
    selectionModelChanged = Signal()
    lineNumberChanged = Signal(int)
    filenameChanged = Signal(str)

    def __init__(self, parent=None, program_model=None, selection_model=None):
        super().__init__(parent)

        self._program_model = program_model
        self._selection_model = selection_model
        self._line_number = 0
        self._filename = ""

        self._sub = rospy.Subscriber(
            PROGRAM_POSITION_TOPIC,
            msg.ProgramPosition,
            self._on_program_position_update_received,
        )
        ensure_cleanup(self._shutdown)

    @Slot()
    def _shutdown(self):
        self._sub.unregister()

    @Property(QObject, notify=programModelChanged)  # QAbstractItemModel
    def programModel(self):
        return self._program_model

    @programModel.setter
    def programModel(self, value):
        if value == self._program_model:
            return
        self._program_model = value
        self.programModelChanged.emit()

    @Property(QObject, notify=selectionModelChanged)  # QItemSelectionModel
    def selectionModel(self):
        return self._selection_model

    @selectionModel.setter
    def selectionModel(self, value):
        if value == self._selection_model:
            return
        self._selection_model = value
        self.selectionModelChanged.emit()

    @Property(int, notify=lineNumberChanged)
    def lineNumber(self):
        return self._line_number

    @Property(str, notify=filenameChanged)
    def filename(self):
        return self._filename

    def _update_position(self, position):
        self._line_number = position.linum
        self.lineNumberChanged.emit(self._line_number)
        self._filename = position.filename
        self.filenameChanged.emit(self._filename)

    def _on_program_position_update_received(self, position):
        position = ProgramPosition(
            linum=position.line_number, filename=position.filename
        )
        if position.filename == '_mdi_command_':
            return

        self._update_position(position)

        if position.filename == '':
            return

        if not self._selection_model:
            return
        if not self._program_model:
            return
        index = self._program_model.index_for_position(position)
        self._selection_model.setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect
        )

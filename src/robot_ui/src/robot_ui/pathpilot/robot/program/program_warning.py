from enum import IntEnum, auto
from PySide6.QtCore import QObject, Property, QEnum, Signal
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramWarning(QObject):
    messageChanged = Signal()
    typeChanged = Signal()

    class Types(IntEnum):
        UnknownType = auto()
        DuplicateName = auto()
        MissingName = auto()
        ShadowsPythonKeyword = auto()
        MissingFunction = auto()
        EmptyProgram = auto()
        EndlessMainLoop = auto()
        FirstLineMovel = auto()

    QEnum(Types)

    def __init__(self, parent=None, message="", type_=Types.UnknownType):
        super().__init__(parent)

        self._message = message
        self._type = type_

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @Property(int, notify=typeChanged)
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if self.type == value:
            return
        self._type = value
        self.typeChanged.emit()

    @message.setter
    def message(self, value):
        if self.message == value:
            return
        self._message = value
        self.messageChanged.emit()

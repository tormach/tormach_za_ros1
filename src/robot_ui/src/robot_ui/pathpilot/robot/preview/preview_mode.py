from enum import IntEnum, auto
from PySide6.QtCore import QObject, QEnum
from PySide6.QtQml import QmlElement, QmlUncreatable


class PreviewModeEnum(IntEnum):
    Interactive = auto()
    View = auto()


QML_IMPORT_NAME = 'pathpilot.robot.preview'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("PreviewMode cannot be created in QML")
class PreviewMode(QObject):
    QEnum(PreviewModeEnum)

from enum import IntEnum
from PySide6.QtCore import QObject, QEnum
from PySide6.QtQml import QmlElement, QmlUncreatable


class PanelEnum(IntEnum):
    Unknown = -1
    MainPanel = 0
    FilePanel = 1
    FramesPanel = 2
    SettingsPanel = 3
    ConversationalPanel = 4
    JogPanel = 5
    StatusPanel = 6


QML_IMPORT_NAME = 'pathpilot.handlers'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("Panels cannot be created in QML")
class Panels(QObject):
    QEnum(PanelEnum)

from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QmlElement

from .signal_handler import SignalHandler

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class LauncherControl(QObject):
    @Slot(str)
    def shutdown(self, reason):
        SignalHandler.shutdown(reason)

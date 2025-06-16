from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtQml import QmlElement

from pp_ros_launch.launcher.internet_checker import check_connection

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class InternetChecker(QObject):
    checkStarted = Signal()
    checkCompleted = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._internet_available = False

    @qasync.asyncSlot()
    async def check(self) -> None:
        self.checkStarted.emit()
        self._internet_available = await check_connection()
        self.checkCompleted.emit(self._internet_available)

    @Property(bool, notify=checkCompleted)
    def internetAvailable(self) -> bool:
        return self._internet_available

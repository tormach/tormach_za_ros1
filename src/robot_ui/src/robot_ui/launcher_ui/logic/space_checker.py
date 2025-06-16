from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtQml import QmlElement

from pp_ros_launch.launcher.space_checker import docker_has_enough_space

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class SpaceChecker(QObject):
    checkStarted = Signal()
    checkCompleted = Signal()
    dockerSpaceAvailableChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._docker_has_enough_space = False

    @qasync.asyncSlot()
    async def check(self) -> None:
        self.checkStarted.emit()
        self._docker_has_enough_space = await docker_has_enough_space()
        self.checkCompleted.emit()
        self.dockerSpaceAvailableChanged.emit(self.dockerSpaceAvailable)

    @Property(bool, notify=dockerSpaceAvailableChanged)
    def dockerSpaceAvailable(self) -> bool:
        return self._docker_has_enough_space

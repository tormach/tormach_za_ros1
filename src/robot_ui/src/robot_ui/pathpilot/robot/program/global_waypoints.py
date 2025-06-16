from PySide6.QtCore import Signal, Slot, QUrl
from PySide6.QtQml import QmlElement

from robot_command.global_waypoints import GlobalWaypoints as GWaypoints

from ...qt_helpers import ensure_cleanup
from .waypoints import Waypoints

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GlobalWaypoints(Waypoints, GWaypoints):
    """Wraps the pure Python GlobalWaypoints class to enable signals and QML
    compatibility."""

    reset = Signal()

    def __init__(self, parent=None, subscribe=True, **kwargs):
        super().__init__(parent=parent, subscribe=subscribe, **kwargs)

        if subscribe:
            ensure_cleanup(self._stop)

    def reset_data(self, waypoints=None):
        super().reset_data(waypoints)
        self.reset.emit()

    @Slot()
    def readFromStore(self):
        super().read_from_store()

    @Slot()
    def writeToStore(self):
        super().write_to_store()

    @Slot(QUrl)
    def importFromFile(self, file_path):
        super().import_from_file(file_path.toLocalFile())

    @Slot(QUrl)
    def exportToFile(self, file_path):
        super().export_to_file(file_path.toLocalFile())

    @Slot()
    def _stop(self):
        super().stop()

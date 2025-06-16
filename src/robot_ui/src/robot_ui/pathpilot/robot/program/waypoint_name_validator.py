from PySide6.QtCore import Property, Signal, QObject
from PySide6.QtQml import QmlElement

from ...core import NameValidator
from .waypoints import Waypoints

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WaypointNameValidator(NameValidator):
    waypointsChanged = Signal()
    namesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._waypoints: Waypoints = None
        self._ignored_name = ''
        self._default_prefix = ''

        self.waypointsChanged.connect(self.namesChanged)

    @Property(QObject, notify=waypointsChanged)  # Waypoints
    def waypoints(self):
        return self._waypoints

    @waypoints.setter
    def waypoints(self, new_waypoints):
        if new_waypoints == self._waypoints:
            return
        self._waypoints = new_waypoints
        self.waypointsChanged.emit()

    @Property('QStringList', notify=namesChanged)
    def names(self):
        if self._waypoints is None:
            return ()
        else:
            return (w.name for w in self._waypoints.waypoints)

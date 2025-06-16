from PySide6.QtCore import QObject, Signal
from PySide6.QtQml import QmlElement, QmlUncreatable

from robot_command.waypoints import Waypoints as RobotWaypoints

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class WaypointsInheritanceAdapter(RobotWaypoints):
    """Allows super inheritance to work with the Waypoints class"""

    def __init__(self, waypoints=None, **_kwargs):
        super().__init__(waypoints)


@QmlElement
@QmlUncreatable("Waypoints cannot be created in QML")
class Waypoints(QObject, WaypointsInheritanceAdapter):
    waypointAboutToBeInserted = Signal(str)
    waypointInserted = Signal(str, str)
    waypointAboutToBeRemoved = Signal(str)
    waypointRemoved = Signal(str)
    waypointUpdated = Signal(str, str)
    waypointsUpdated = Signal()

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

    def create_waypoint(self, uuid=None):
        before_uuid = self.waypoints[-1].uuid if any(self.waypoints) else ''
        self.waypointAboutToBeInserted.emit(before_uuid)
        new_waypoint = super().create_waypoint(uuid=uuid)
        self.waypointInserted.emit(before_uuid, new_waypoint.uuid)
        self.waypointsUpdated.emit()
        return new_waypoint

    def remove_waypoint(self, waypoint):
        uuid = waypoint.uuid
        self.waypointAboutToBeRemoved.emit(uuid)
        super().remove_waypoint(waypoint)
        self.waypointRemoved.emit(uuid)
        self.waypointsUpdated.emit()

    def update_waypoint(self, waypoint, property_, value):
        super().update_waypoint(waypoint, property_, value)
        self.waypointUpdated.emit(waypoint.uuid, property_)
        self.waypointsUpdated.emit()

import contextlib

from PySide6.QtCore import Property, Signal
from PySide6.QtQml import QmlElement

from .waypoints_manipulator import WaypointsManipulator
from .global_waypoints import GlobalWaypoints

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GlobalWaypointsManipulator(WaypointsManipulator):
    """Manipulates the global waypoints and stores the modification history"""

    _source = None  # type: GlobalWaypoints

    sourceWaypointsChanged = Signal(GlobalWaypoints)
    modifiedWaypointsChanged = Signal(GlobalWaypoints)

    def __init__(self, parent=None, source_global_waypoints=None):
        super().__init__(parent)

        self._source = source_global_waypoints
        self._modified = GlobalWaypoints(subscribe=False)

        self.sourceWaypointsChanged.connect(self.resetHistory)

    @Property(GlobalWaypoints, notify=sourceWaypointsChanged)
    def sourceWaypoints(self):
        return self._source

    @sourceWaypoints.setter
    def sourceWaypoints(self, value):
        if value == self._source:
            return
        old_value = self._source
        self._source = value
        self.sourceWaypointsChanged.emit(value)

        if old_value:
            with contextlib.suppress(
                RuntimeError
            ):  # might be called on destruction
                old_value.reset.disconnect(self.resetHistory)
        if value:
            value.reset.connect(self.resetHistory)

    @Property(GlobalWaypoints, notify=modifiedWaypointsChanged)
    def modifiedWaypoints(self):
        return self._modified

    @modifiedWaypoints.setter
    def modifiedWaypoints(self, value):
        if value == self._modified:
            return
        self._modified = value
        self.modifiedWaypointsChanged.emit(value)

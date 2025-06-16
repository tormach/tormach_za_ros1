import contextlib

from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    Slot,
    QEnum,
)
from PySide6.QtQml import QmlElement

from robot_command.waypoint import TargetType
from movej_ik_server.arm_configs import ArmConfigType
from .waypoints import Waypoints


QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WaypointData(QObject):
    """
    Provides a read-only interface to the data of a waypoint for QML.
    This component is meant to be used in combination with the  WaypointTableModel.
    """

    _source = None  # type: Waypoints

    QEnum(TargetType)
    QEnum(ArmConfigType)

    sourceChanged = Signal()
    uuidChanged = Signal(str)
    validChanged = Signal()
    nameChanged = Signal()
    targetChanged = Signal()
    targetTypeChanged = Signal()
    frameChanged = Signal()
    armConfigChanged = Signal()
    revCountChanged = Signal()
    dataChanged = Signal()

    def __init__(self, parent=None, uuid='', source=None):
        super().__init__(parent)

        self._uuid = uuid
        self._source: Waypoints = source

        self.uuidChanged.connect(self.dataChanged)
        self.sourceChanged.connect(self.dataChanged)
        self.dataChanged.connect(self.nameChanged)
        self.dataChanged.connect(self.validChanged)
        self.dataChanged.connect(self.targetChanged)
        self.dataChanged.connect(self.targetTypeChanged)
        self.dataChanged.connect(self.frameChanged)
        self.dataChanged.connect(self.armConfigChanged)
        self.dataChanged.connect(self.revCountChanged)

    @Property(QObject, notify=sourceChanged)  # Waypoints
    def source(self):
        return self._source

    @source.setter
    def source(self, new_source):
        if new_source == self._source:
            return
        old_source, self._source = self._source, new_source
        self.sourceChanged.emit()
        if old_source:
            with contextlib.suppress(RuntimeError):
                old_source.waypointUpdated.disconnect(self._on_waypoint_updated)
                old_source.waypointRemoved.disconnect(self._on_waypoint_removed)
                old_source.reset.disconnect(self._on_source_reset)
        if new_source:
            new_source.waypointUpdated.connect(self._on_waypoint_updated)
            new_source.waypointRemoved.connect(self._on_waypoint_removed)
            new_source.reset.connect(self._on_source_reset)

    @Property(bool, notify=validChanged)
    def valid(self):
        if not self._source:
            return False
        return self._source.get_waypoint(self._uuid) is not None

    @Property(str, notify=uuidChanged)
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if value == self._uuid:
            return
        self._uuid = value
        self.uuidChanged.emit(value)

    @Property(str, notify=nameChanged)
    def name(self):
        return self._get_attribute('name', '')

    @Property(list, notify=targetChanged)
    def target(self):
        return self._get_attribute('target', [])

    @Property(int, notify=targetTypeChanged)
    def targetType(self):
        return self._get_attribute('target_type', TargetType.Pose)

    @Property(str, notify=frameChanged)
    def frame(self):
        return self._get_attribute('frame', '')

    @Property(int, notify=armConfigChanged)
    def armConfig(self):
        return self._get_attribute('arm_config', ArmConfigType.AnyConfig)

    @Property(int, notify=revCountChanged)
    def revCount(self):
        return self._get_attribute('rev_count', None)  # TODO: 0 or None?

    def _get_attribute(self, name, default):
        if not self._source:
            return default
        waypoint = self._source.get_waypoint(self._uuid)
        if not waypoint:
            return default
        return getattr(waypoint, name, default)

    @Slot(str, str)
    def _on_waypoint_updated(self, uuid, _property):
        if uuid == self._uuid:
            self.dataChanged.emit()

    @Slot(str)
    def _on_waypoint_removed(self, uuid):
        if uuid == self._uuid:
            self.dataChanged.emit()

    @Slot()
    def _on_source_reset(self):
        self.dataChanged.emit()

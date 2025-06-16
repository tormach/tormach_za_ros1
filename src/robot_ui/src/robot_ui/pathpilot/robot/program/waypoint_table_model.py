from enum import IntEnum, auto
from typing import Optional

from PySide6.QtCore import (
    QByteArray,
    Qt,
    QEnum,
    Signal,
    Property,
    Slot,
    QModelIndex,
    QObject,
)
from PySide6.QtQml import QJSValue, QmlElement

from ...models.model_index_walker import ModelIndexWalker
from ...models.base_table_model import (
    BaseTableModel,
)
from robot_command.waypoint import TargetType
from .waypoints import Waypoints

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WaypointTableModel(BaseTableModel):
    class Roles(IntEnum):
        SortRole = Qt.UserRole
        TypeRole = auto()
        NumberRole = auto()
        AxisRole = auto()
        FirstDataRole = auto()  # here begins the data field roles
        NameRole = auto()
        TargetTypeRole = auto()
        TargetRole = auto()
        FrameRole = auto()
        UuidRole = auto()
        ModifiedRole = auto()
        XRole = auto()
        YRole = auto()
        ZRole = auto()
        ARole = auto()
        BRole = auto()
        CRole = auto()
        ConfigRole = auto()
        RevCountRole = auto()
        WarningRole = auto()
        LastDataRole = auto()

    QEnum(Roles)
    QEnum(TargetType)

    _ROLE_NAMES = {
        Roles.SortRole: QByteArray(b'sort'),
        Roles.TypeRole: QByteArray(b'type'),
        Roles.NumberRole: QByteArray(b'number'),
        Roles.AxisRole: QByteArray(b'axis'),
        Roles.NameRole: QByteArray(b'name'),
        Roles.TargetTypeRole: QByteArray(b'targetType'),
        Roles.TargetRole: QByteArray(b'target'),
        Roles.FrameRole: QByteArray(b'frame'),
        Roles.UuidRole: QByteArray(b'uuid'),
        Roles.ModifiedRole: QByteArray(b'modified'),
        Roles.XRole: QByteArray(b'x'),
        Roles.YRole: QByteArray(b'y'),
        Roles.ZRole: QByteArray(b'z'),
        Roles.ARole: QByteArray(b'a'),
        Roles.BRole: QByteArray(b'b'),
        Roles.CRole: QByteArray(b'c'),
        Roles.ConfigRole: QByteArray(b'config'),
        Roles.RevCountRole: QByteArray(b'rev'),
        Roles.WarningRole: QByteArray(b'warning'),
    }

    sourceChanged = Signal()
    warningsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._waypoints = []
        self._source: Optional[Waypoints] = None
        self._uuid_index_map = {}
        self._warnings = {}

        self._role_names.update(self._ROLE_NAMES)

        self.sourceChanged.connect(self._on_source_reset)

    @Property(QObject, notify=sourceChanged)  # Waypoints
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if value == self._source:
            return
        if self._source:
            self._source.disconnect(self)  # disconnect all signals
        self._source = value
        if self._source:
            self._source.reset.connect(self._on_source_reset)
            self._source.waypointAboutToBeInserted.connect(
                self._on_waypoint_about_to_be_inserted
            )
            self._source.waypointInserted.connect(self._on_waypoint_inserted)
            self._source.waypointAboutToBeRemoved.connect(
                self._on_waypoint_about_to_be_removed
            )
            self._source.waypointRemoved.connect(self._on_waypoint_removed)
            self._source.waypointUpdated.connect(self._on_waypoint_updated)

        self.sourceChanged.emit()

    @Property('QVariant', notify=warningsChanged)
    def warnings(self):
        return self._warnings

    @warnings.setter
    def warnings(self, warnings):
        warnings = (
            warnings.toVariant() if isinstance(warnings, QJSValue) else warnings
        )
        if warnings == self._warnings:
            return

        old_warnings = self._warnings
        self._warnings = warnings
        for uuid in warnings:
            index = self.index_for_uuid(uuid)
            if index.isValid():
                end_index = self.index(index.row(), self.columnCount() - 1)
                self.dataChanged.emit(
                    index, end_index, [self.Roles.WarningRole]
                )
        for uuid in old_warnings.keys() - warnings.keys():
            index = self.index_for_uuid(uuid)
            if index.isValid():
                end_index = self.index(index.row(), self.columnCount() - 1)
                self.dataChanged.emit(
                    index, end_index, [self.Roles.WarningRole]
                )

        self.warningsChanged.emit()

    @Slot()
    def _on_source_reset(self):
        self.beginResetModel()
        self._waypoints = self._source.waypoints if self._source else []
        self._update_uuid_index_map()
        self.endResetModel()

    @Slot(str)
    def _on_waypoint_about_to_be_inserted(self, before_uuid):
        if before_uuid != '':
            index = self.index_for_uuid(before_uuid)
            row = index.row() + 1
        else:
            row = 0

        self.beginInsertRows(QModelIndex(), row, row)

    @Slot(str, str)
    def _on_waypoint_inserted(self, _before_uuid, _new_uuid):
        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endInsertRows()

    @Slot(str)
    def _on_waypoint_about_to_be_removed(self, uuid):
        index = self.index_for_uuid(uuid)
        row = index.row()
        self.beginRemoveRows(QModelIndex(), row, row)

    @Slot(str)
    def _on_waypoint_removed(self, _uuid):
        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endRemoveRows()

    @Slot(str, str)
    def _on_waypoint_updated(self, _uuid, _property):
        index = self.index_for_uuid(_uuid)
        end_index = self.index(index.row(), self.columnCount() - 1)
        self.dataChanged.emit(index, end_index)

    def _update_uuid_index_map(self):
        self._uuid_index_map = {}

        for index in ModelIndexWalker(self, QModelIndex()):
            waypoint = index.internalPointer()
            uuid = waypoint.uuid
            self._uuid_index_map[uuid] = index

    def index_for_uuid(self, uuid):
        return self._uuid_index_map.get(uuid, QModelIndex())

    def data(self, index, role):
        if not index.isValid():
            return

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        # model index: row, colum, parent
        # role: which kind of data to fetch

        if role == Qt.DisplayRole:
            tmp = self.data(index, field)

            if field == self.Roles.ConfigRole and tmp is None:
                return ''
            if field == self.Roles.RevCountRole and tmp is None:
                return ''

            return str(tmp)
        elif role == self.Roles.NumberRole:
            if self.Roles.XRole <= field <= self.Roles.CRole:
                return self.data(index, field)
            else:
                return -1
        elif role == self.Roles.AxisRole:
            if self.Roles.XRole <= field <= self.Roles.CRole:
                return field - self.Roles.XRole
            else:
                return -1
        elif role >= self.Roles.FirstDataRole:
            return self._get_data(index, role)
        elif role == Qt.InitialSortOrderRole:
            return Qt.AscendingOrder
        elif role == self.Roles.SortRole:
            return self.data(index, field)
        elif role == self.Roles.TypeRole:
            if self.Roles.XRole <= field <= self.Roles.ZRole:
                waypoint = index.internalPointer()
                return (
                    'linear_number'
                    if waypoint.target_type == TargetType.Pose
                    else 'angular_number'
                )
            elif self.Roles.ARole <= field <= self.Roles.CRole:
                return 'angular_number'
            else:
                return self._role_names.get(field, None)
        else:
            return None

    def _get_data(self, index, role):
        waypoint = index.internalPointer()
        switch = {
            self.Roles.NameRole: lambda: waypoint.name,
            self.Roles.TargetTypeRole: lambda: waypoint.target_type,
            self.Roles.TargetRole: lambda: waypoint.target,
            self.Roles.FrameRole: lambda: waypoint.frame,
            self.Roles.UuidRole: lambda: waypoint.uuid,
            self.Roles.ModifiedRole: lambda: waypoint.modified,
            self.Roles.XRole: lambda: waypoint.target[0],
            self.Roles.YRole: lambda: waypoint.target[1],
            self.Roles.ZRole: lambda: waypoint.target[2],
            self.Roles.ARole: lambda: waypoint.target[3],
            self.Roles.BRole: lambda: waypoint.target[4],
            self.Roles.CRole: lambda: waypoint.target[5],
            self.Roles.ConfigRole: lambda: waypoint.arm_config,
            self.Roles.RevCountRole: lambda: waypoint.rev_count,
            self.Roles.WarningRole: lambda: self._warnings.get(
                waypoint.uuid, []
            ),
        }
        return switch.get(role, lambda: None)()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._waypoints)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._waypoints[row]
        except (IndexError, AttributeError):
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

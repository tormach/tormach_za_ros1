from enum import IntEnum, auto
import attr
from PySide6.QtCore import (
    Qt,
    QByteArray,
    QModelIndex,
    QEnum,
)
from PySide6.QtQml import QJSValue, QmlElement

from robot_command.interfaces import MachinetalkInterfaceSingleton
from ros_machinetalk import InstanceClient  # noqa: F401

from ...qt_helpers import MultiSlot
from ...models.base_table_model import (
    BaseTableModel,
)
from ...models.model_index_walker import ModelIndexWalker

QML_IMPORT_NAME = 'pathpilot.robot.machinetalk'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@attr.s
class Node:
    name = attr.ib(type=str)
    uuid = attr.ib(type=str)
    pose = attr.ib(type=list)


@QmlElement
class MachinetalkNodeTableModel(BaseTableModel):
    class Roles(IntEnum):
        SortRole = Qt.UserRole
        TypeRole = auto()
        NumberRole = auto()
        AxisRole = auto()
        FirstDataRole = auto()  # here begins the data field roles
        NameRole = auto()
        UuidRole = auto()
        PoseRole = auto()
        XRole = auto()
        YRole = auto()
        ZRole = auto()
        ARole = auto()
        BRole = auto()
        CRole = auto()
        LastDataRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.SortRole: QByteArray(b'sort'),
        Roles.TypeRole: QByteArray(b'type'),
        Roles.NumberRole: QByteArray(b'number'),
        Roles.AxisRole: QByteArray(b'axis'),
        Roles.NameRole: QByteArray(b'name'),
        Roles.UuidRole: QByteArray(b'uuid'),
        Roles.PoseRole: QByteArray(b'pose'),
        Roles.XRole: QByteArray(b'x'),
        Roles.YRole: QByteArray(b'y'),
        Roles.ZRole: QByteArray(b'z'),
        Roles.ARole: QByteArray(b'a'),
        Roles.BRole: QByteArray(b'b'),
        Roles.CRole: QByteArray(b'c'),
    }

    _instance_client = None  # type: InstanceClient

    def __init__(self, parent=None):
        super().__init__(parent)

        self._interface = MachinetalkInterfaceSingleton()
        self._instance_client = self._interface.instance_client
        self._instance_client.on_nodes_changed.append(self._update_model)
        self._instance_client.on_nodes_changed.append(self._update_model)
        self.destroyed.connect(
            lambda: self._instance_client.on_nodes_changed.remove(
                self._update_model
            )
        )
        self._node_uuids = set()
        self._uuid_index_map = {}
        self._nodes = []

        self._role_names.update(self._ROLE_NAMES)

        self._update_model()

    @MultiSlot(str, str, [QJSValue, list])
    def updateNode(self, name, uuid, pose):
        """
        Updates a node from the Machinetalk node of the current ROS instance.
        """
        pose = pose.toVariant() if isinstance(pose, QJSValue) else pose
        return self._instance_client.update_node(
            name=name, uuid=uuid, pose=pose
        )

    def _update_model(self):
        self.beginResetModel()
        self._node_uuids = set()
        self._nodes = []

        for node in self._instance_client.nodes:
            pose = node['pose'] if 'pose' in node else [0] * 6
            nodes = Node(name=node['name'], uuid=node['uuid'], pose=pose)
            self._nodes.append(nodes)
            self._node_uuids.add(node['uuid'])

        self._update_uuid_index_map()
        self.endResetModel()

    def _update_uuid_index_map(self):
        self._uuid_index_map = {}

        for index in ModelIndexWalker(self, QModelIndex()):
            node = index.internalPointer()
            uuid = node.uuid
            self._uuid_index_map[uuid] = index

    def data(self, index, role):
        if not index.isValid():
            return None

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole:
            return str(self.data(index, field))
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
            node = index.internalPointer()
            switch = {
                self.Roles.NameRole: lambda: node.name,
                self.Roles.UuidRole: lambda: node.uuid,
                self.Roles.PoseRole: lambda: node.pose,
                self.Roles.XRole: lambda: node.pose[0],
                self.Roles.YRole: lambda: node.pose[1],
                self.Roles.ZRole: lambda: node.pose[2],
                self.Roles.ARole: lambda: node.pose[3],
                self.Roles.BRole: lambda: node.pose[4],
                self.Roles.CRole: lambda: node.pose[5],
            }
            return switch.get(role, lambda: None)()
        elif role == Qt.InitialSortOrderRole:
            return Qt.AscendingOrder
        elif role == self.Roles.SortRole:
            return self.data(index, field)
        elif role == self.Roles.TypeRole:
            if self.Roles.XRole <= field <= self.Roles.ZRole:
                return 'linear_number'
            elif self.Roles.ARole <= field <= self.Roles.CRole:
                return 'angular_number'
            else:
                return self._role_names.get(field, None)
        else:
            return None

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._nodes)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._nodes[row]
        except (IndexError, AttributeError):
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

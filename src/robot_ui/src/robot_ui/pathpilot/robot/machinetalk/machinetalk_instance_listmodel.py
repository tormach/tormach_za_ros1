import attr
from enum import IntEnum, auto

from PySide6.QtCore import (
    Slot,
    Qt,
    QAbstractItemModel,
    QByteArray,
    QModelIndex,
    QEnum,
)
from PySide6.QtQml import QmlElement


from robot_command.interfaces import MachinetalkInterfaceSingleton
from ros_machinetalk import InstanceClient  # noqa: F401

from ...models.model_index_walker import ModelIndexWalker

QML_IMPORT_NAME = 'pathpilot.robot.machinetalk'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@attr.s
class InstanceNode:
    name = attr.ib(type=str)
    uuid = attr.ib(type=str)
    host_name = attr.ib(type=str)
    version = attr.ib(type=str)
    selected = attr.ib(type=bool)


@QmlElement
class MachinetalkInstanceListModel(QAbstractItemModel):
    class Roles(IntEnum):
        NameRole = Qt.UserRole
        UuidRole = auto()
        HostNameRole = auto()
        VersionRole = auto()
        SelectedRole = auto()
        ConnectedRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.NameRole: QByteArray(b'name'),
        Roles.UuidRole: QByteArray(b'uuid'),
        Roles.HostNameRole: QByteArray(b'hostname'),
        Roles.VersionRole: QByteArray(b'version'),
        Roles.SelectedRole: QByteArray(b'selected'),
        Roles.ConnectedRole: QByteArray(b'connected'),
    }

    _instance_client = None  # type: InstanceClient

    def __init__(self, parent=None):
        super().__init__(parent)

        self._interface = MachinetalkInterfaceSingleton()
        self._instance_client = self._interface.instance_client
        self._instance_client.on_instances_changed.append(self._update_model)
        self.destroyed.connect(
            lambda: self._instance_client.on_instances_changed.remove(
                self._update_model
            )
        )
        self._instance_client.on_nodes_changed.append(self._update_model)
        self.destroyed.connect(
            lambda: self._instance_client.on_nodes_changed.remove(
                self._update_model
            )
        )
        self._interface.on_connected_changed.append(self._on_connected_changed)
        self.destroyed.connect(
            lambda: self._interface.on_connected_changed.remove(
                self._on_connected_changed
            )
        )

        self._instance_nodes = []
        self._node_uuids = set()
        self._uuid_index_map = {}

        self._update_model()

    @Slot(str, str)
    def addNode(self, name, uuid):
        """Adds a new node to the Machinetalk nodes of the current ROS instance."""
        return self._instance_client.add_node(
            name=name, uuid=uuid, pose=[0.0] * 6
        )

    @Slot(str, str)
    def updateNode(self, name, uuid):
        """Updates a node from the Machinetalk node of the current ROS instance."""
        return self._instance_client.update_node(
            name=name, uuid=uuid, pose=[0.0] * 6
        )

    @Slot(str)
    def removeNode(self, uuid):
        """Removes a node from the Machinetalk nodes of the current ROS instance."""
        return self._instance_client.remove_node(uuid=uuid)

    def _on_connected_changed(self, _connected, uuid):
        index = self._uuid_index_map.get(uuid, QModelIndex())
        self.dataChanged.emit(index, index)

    def _update_model(self):
        self.beginResetModel()
        self._node_uuids = set()
        self._instance_nodes = []
        for node in self._instance_client.nodes:
            instance = InstanceNode(
                name=node['name'],
                uuid=node['uuid'],
                host_name='',
                version='',
                selected=True,
            )
            self._instance_nodes.append(instance)
            self._node_uuids.add(node['uuid'])
        for instance in self._instance_client.instances:
            if instance.name.startswith("HAL-IO Sim"):  # ignore IO sim instance
                continue
            if instance.uuid in self._node_uuids:
                for node in self._instance_nodes:
                    if node.uuid == instance.uuid:
                        node.version = instance.version
                        node.host_name = instance.host_name
                        break
            else:
                instance_node = InstanceNode(
                    name=instance.name,
                    uuid=instance.uuid,
                    host_name=instance.host_name,
                    version=instance.version,
                    selected=False,
                )
                self._instance_nodes.append(instance_node)
        self._update_uuid_index_map()
        self.endResetModel()

    def _update_uuid_index_map(self):
        self._uuid_index_map = {}

        for index in ModelIndexWalker(self, QModelIndex()):
            node = index.internalPointer()
            uuid = node.uuid
            self._uuid_index_map[uuid] = index

    def parent(self, _index):
        return QModelIndex()

    def data(self, index, role):
        if not index.isValid():
            return
        if role < Qt.UserRole:
            return None

        instance = index.internalPointer()

        switch = {
            self.Roles.NameRole: lambda: instance.name,
            self.Roles.UuidRole: lambda: instance.uuid,
            self.Roles.HostNameRole: lambda: instance.host_name,
            self.Roles.VersionRole: lambda: instance.version,
            self.Roles.SelectedRole: lambda: instance.selected,
            self.Roles.ConnectedRole: lambda: instance.selected
            and self._interface.is_connected(uuid=instance.uuid),
        }

        return switch.get(role, lambda: None)()

    def columnCount(self, _parent):
        return len(self._ROLE_NAMES)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._instance_nodes)

    def roleNames(self):
        return self._ROLE_NAMES

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._instance_nodes[row]
        except (IndexError, AttributeError):
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

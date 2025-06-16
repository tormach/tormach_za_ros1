import logging
from enum import IntEnum, auto
from . import qt_launcher_release_channel_helper

from PySide6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    Qt,
    QModelIndex,
    QEnum,
    Signal,
    Property,
)
from PySide6.QtQml import QmlElement

from pp_ros_launch.launcher.updates import Updater

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class LocalChannels(QAbstractItemModel):
    class Roles(IntEnum):
        LabelRole = Qt.UserRole
        NameRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.LabelRole: QByteArray(b'label'),
        Roles.NameRole: QByteArray(b'name'),
    }

    loadingStarted = Signal()
    loadingCompleted = Signal()
    defaultIndexChanged = Signal(int)

    multipleChanged = Signal()

    logger = logging.getLogger('launcher.local_channels')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._default_index = 0
        self._pathpilot_channels = list()

    @qasync.asyncSlot()
    async def loadChannels(self) -> None:
        self.loadingStarted.emit()
        self.logger.debug("Retrieving local PathPilot Robot Channels")
        self.beginResetModel()
        self._pathpilot_channels.clear()
        self._pathpilot_channels = await Updater.get_local_channels()
        self.logger.info(
            f"Retrieved local channels {[ch for ch in self._pathpilot_channels]}"
        )
        self.endResetModel()
        self.loadingCompleted.emit()
        self.multipleChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._pathpilot_channels):
            return None

        _channel = self._pathpilot_channels[index.row()]
        if not _channel:
            self.logger.error(
                'When quierying for data, the channel was not found! '
                f'Index row: "{index.row()}", channels cache: "{self._pathpilot_channels}"'
            )
        switch = {
            Qt.DisplayRole: lambda: qt_launcher_release_channel_helper.get_label(
                _channel, self
            ),
            self.Roles.LabelRole: lambda: qt_launcher_release_channel_helper.get_label(
                _channel, self
            ),
            self.Roles.NameRole: lambda: qt_launcher_release_channel_helper.get_raw_name(
                _channel, self
            ),
        }

        return switch.get(role, lambda: None)()

    def roleNames(self):
        return self._ROLE_NAMES

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        return self._ROLE_NAMES.get(role, '').title()

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._pathpilot_channels[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

    def parent(self, _index):
        return QModelIndex()

    def columnCount(self, _parent):
        return len(self._ROLE_NAMES)

    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            return len(self._pathpilot_channels)
        else:
            return 0

    @Property(bool, notify=multipleChanged)
    def multiple(self) -> bool:
        return len(self._pathpilot_channels) > 1

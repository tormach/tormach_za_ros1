from datetime import datetime

from PySide6.QtCore import (
    Qt,
    QEnum,
    Signal,
    Property,
    QModelIndex,
    Slot,
    QDate,
    QDateTime,
    QTime,
    QLocale,
)
from PySide6.QtQml import QmlElement

from .hub_connector import HubConnector
from ..file.flat_filesystem_model import FlatFileSystemModel

from ..file.file_utils import human_readable_bytes
from ..models.base_table_model import (
    BaseTableModel,
)

QML_IMPORT_NAME = 'pathpilot.hub'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class HubFileSystemModel(BaseTableModel):
    Roles = FlatFileSystemModel.Roles
    QEnum(Roles)

    rootPathChanged = Signal(str)
    hubConnectorChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_path = ''
        self._items = []
        self._hub_connector = None

        self._role_names.update(FlatFileSystemModel._ROLE_NAMES)

        self.rootPathChanged.connect(self._update_items)

    @Property(str, notify=rootPathChanged)
    def rootPath(self):
        return self._root_path

    @rootPath.setter
    def rootPath(self, value):
        if value == self._root_path:
            return
        self._root_path = value
        self.rootPathChanged.emit(value)

    @Property(HubConnector, notify=hubConnectorChanged)
    def hubConnector(self):
        return self._hub_connector

    @hubConnector.setter
    def hubConnector(self, value):
        if value == self._hub_connector:
            return
        self._hub_connector = value
        self.hubConnectorChanged.emit()

    @Slot()
    def reload(self):
        self._update_items()

    @Slot()
    def _update_items(self):
        data = (
            self._hub_connector.get_files_for_path(self._root_path)
            if self._hub_connector
            else []
        )
        self.beginResetModel()
        self._items = data
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole or role >= self.Roles.FirstDataRole:
            return self._file_data(item, role, field)
        elif role == Qt.InitialSortOrderRole:
            if field in (self.Roles.SizeRole, self.Roles.LastModifiedRole):
                return Qt.DescendingOrder
            else:
                return Qt.AscendingOrder
        elif role == self.Roles.SortRole:
            return self.data(index, field)
        elif role == self.Roles.TypeRole:
            return self._role_names.get(field, None)
        else:
            return None

    def _file_data(self, item, role, field):
        switch = {
            self.Roles.FileNameRole: lambda: item.get('name', ''),
            self.Roles.IsDirRole: lambda: item.get('type', 'f') == 'd',
            self.Roles.PathRole: lambda: item.get('fullpath', ''),
        }
        switch.update(
            {
                self.Roles.SizeRole: lambda: self._size_string(
                    item.get('size', None)
                ),
                self.Roles.LastModifiedRole: lambda: self._date_string(
                    item.get('mtime_utc', None)
                ),
            }
            if role == Qt.DisplayRole
            else {
                self.Roles.SizeRole: lambda: item.get('size', 0),
                self.Roles.LastModifiedRole: lambda: self._data_stamp(
                    item.get('mtime_utc', None)
                ),
            }
        )
        data = switch.get(field, lambda: None)()
        return str(data) if role == Qt.DisplayRole else data

    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            return len(self._items)
        else:
            return 0

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._items[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

    @staticmethod
    def _date_string(mtime_utc):
        if mtime_utc is None:
            return ""
        utcdatetime = datetime.strptime(mtime_utc, '%Y-%m-%d %H:%M:%S.%f')
        date = QDate(utcdatetime.year, utcdatetime.month, utcdatetime.day)
        time = QTime(
            utcdatetime.hour,
            utcdatetime.minute,
            utcdatetime.second,
            utcdatetime.microsecond // 1000,
        )
        datetime_ = QDateTime(date, time, Qt.UTC)
        local_dt = datetime_.toLocalTime()
        locale = QLocale.system()
        if QDate.currentDate() == local_dt.date():
            return locale.toString(local_dt.time(), QLocale.ShortFormat)
        else:
            return locale.toString(local_dt.date(), QLocale.ShortFormat)

    @staticmethod
    def _date_stamp(mtime_utc):
        if mtime_utc is None:
            return 0
        utcdatetime = datetime.strptime(mtime_utc, '%Y-%m-%d %H:%M:%S.%f')
        return utcdatetime.timestamp()

    @staticmethod
    def _size_string(bytes):
        if bytes is None:
            return ""
        else:
            return human_readable_bytes(bytes)

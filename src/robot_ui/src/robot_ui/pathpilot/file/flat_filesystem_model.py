import os
from enum import IntEnum, auto
from PySide6.QtCore import (
    QByteArray,
    Qt,
    QEnum,
    Signal,
    Property,
    QModelIndex,
    QFileInfo,
    Slot,
    QDate,
    QLocale,
)
from PySide6.QtQml import QmlElement

from .file_utils import human_readable_bytes
from ..models.base_table_model import (
    BaseTableModel,
)


QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


# noinspection PyMethodOverriding
@QmlElement
class FlatFileSystemModel(BaseTableModel):
    class Roles(IntEnum):
        SortRole = Qt.UserRole
        TypeRole = auto()
        FirstDataRole = auto()  # here begins the data field roles
        FileNameRole = auto()
        SizeRole = auto()
        LastModifiedRole = auto()
        IsDirRole = auto()
        PathRole = auto()
        LastDataRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.SortRole: QByteArray(b'sort'),
        Roles.TypeRole: QByteArray(b'type'),
        Roles.FileNameRole: QByteArray(b'fileName'),
        Roles.SizeRole: QByteArray(b'size'),
        Roles.LastModifiedRole: QByteArray(b'lastModified'),
        Roles.IsDirRole: QByteArray(b'isDir'),
        Roles.PathRole: QByteArray(b'path'),
    }

    rootPathChanged = Signal(str)
    ignoreHiddenChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_path = ''
        self._ignore_hidden = True
        self._items = []

        self._role_names.update(self._ROLE_NAMES)

        self.rootPathChanged.connect(self._update_items)
        self.ignoreHiddenChanged.connect(self._update_items)

    @Property(str, notify=rootPathChanged)
    def rootPath(self):
        return self._root_path

    @rootPath.setter
    def rootPath(self, value):
        if value == self._root_path:
            return
        self._root_path = value
        self.rootPathChanged.emit(value)

    @Property(bool, notify=ignoreHiddenChanged)
    def ignoreHidden(self):
        return self._ignore_hidden

    @ignoreHidden.setter
    def ignoreHidden(self, value):
        if value == self._ignore_hidden:
            return
        self._ignore_hidden = value
        self.ignoreHiddenChanged.emit(value)

    @Slot()
    def reload(self):
        self._update_items()

    @Slot()
    def _update_items(self):
        self.beginResetModel()
        try:
            items = os.listdir(os.path.expanduser(self._root_path))
        except OSError:
            self._items = []
        else:
            if self._ignore_hidden:
                self._items = [i for i in items if not i.startswith('.')]
            else:
                self._items = items
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        file_name = index.internalPointer()
        file_path = os.path.join(os.path.expanduser(self._root_path), file_name)
        if not os.path.exists(file_path):
            return None

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole or role >= self.Roles.FirstDataRole:
            return self._file_data(file_path, role, field)
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

    def _file_data(self, file_path, role, field):
        file_info = QFileInfo(file_path)
        switch = {
            self.Roles.FileNameRole: lambda: file_info.fileName(),
            self.Roles.IsDirRole: lambda: file_info.isDir(),
            self.Roles.PathRole: lambda: file_info.filePath(),
        }
        switch.update(
            {
                self.Roles.SizeRole: lambda: self._size_string(file_info),
                self.Roles.LastModifiedRole: lambda: self._date_string(
                    file_info
                ),
            }
            if role == Qt.DisplayRole
            else {
                self.Roles.SizeRole: lambda: self._size(file_info),
                self.Roles.LastModifiedRole: lambda: file_info.lastModified().toMSecsSinceEpoch(),
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
    def _date_string(fi):
        last_modified = fi.lastModified()
        locale = QLocale.system()
        if QDate.currentDate() == last_modified.date():
            return locale.toString(last_modified.time(), QLocale.ShortFormat)
        else:
            return locale.toString(last_modified.date(), QLocale.ShortFormat)

    def _size_string(self, fi):
        if fi.isDir():
            try:
                items = len(os.listdir(fi.filePath()))
            except PermissionError:
                return self.tr('N/A')
            if items == 1:
                return self.tr('{} item').format(items)
            else:
                return self.tr('{} items').format(items)
        num = fi.size()
        return human_readable_bytes(num)

    @staticmethod
    def _size(fi):
        if fi.isDir():
            return len(os.listdir(fi.filePath()))
        else:
            return fi.size()

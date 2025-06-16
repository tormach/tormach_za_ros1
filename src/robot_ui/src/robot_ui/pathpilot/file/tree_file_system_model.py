import os
from itertools import chain
from enum import IntEnum, auto
from collections import namedtuple

from PySide6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    Qt,
    QEnum,
    Signal,
    Property,
    QModelIndex,
    QFileInfo,
    Slot,
    QDate,
)
from PySide6.QtQml import QmlElement

from .flat_filesystem_model import FlatFileSystemModel

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

FileTreeItem = namedtuple('FileTreeItem', 'parent children path row')


@QmlElement
class TreeFileSystemModel(QAbstractItemModel):
    class _AdditionalRoles(IntEnum):
        DisplaySizeRole = FlatFileSystemModel.Roles.LastDataRole + 1
        DisplayLastModifiedRole = auto()

    Roles = IntEnum(
        'Roles',
        [
            (n.name, n.value)
            for n in chain(FlatFileSystemModel.Roles, _AdditionalRoles)
        ],
    )
    QEnum(Roles)

    _ROLE_NAMES = {
        _AdditionalRoles.DisplaySizeRole: QByteArray(b'displaySize'),
        _AdditionalRoles.DisplayLastModifiedRole: QByteArray(
            b'displayLastModified'
        ),
    }

    rootPathChanged = Signal(str)
    ignoreHiddenChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_path = ''
        self._root_item = None
        self._ignore_hidden = True

        self._role_names = QAbstractItemModel.roleNames(self)
        self._role_names.update(FlatFileSystemModel._ROLE_NAMES)
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
        root_path = os.path.expanduser(self._root_path)
        root_item = FileTreeItem(
            parent=None, children=[], path=root_path, row=0
        )
        dir_item_map = {root_path: root_item}
        try:
            for root, dirs, files in os.walk(root_path):
                root_abs_path = os.path.join(root_path, root)
                parent_item = dir_item_map[root_abs_path]
                if self._ignore_hidden:
                    files = [f for f in files if f[0] != '.']
                    dirs[:] = [d for d in dirs if d[0] != '.']
                for dir_ in dirs:
                    abs_path = os.path.join(root_abs_path, dir_)
                    item = FileTreeItem(
                        parent=parent_item,
                        children=[],
                        path=abs_path,
                        row=len(parent_item.children),
                    )
                    parent_item.children.append(item)
                    dir_item_map[abs_path] = item
                for file_ in files:
                    abs_path = os.path.join(root_abs_path, file_)
                    item = FileTreeItem(
                        parent=parent_item,
                        children=[],
                        path=abs_path,
                        row=len(parent_item.children),
                    )
                    parent_item.children.append(item)
        except OSError:
            pass
        self._root_item = root_item
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        tree_item = index.internalPointer()
        if not os.path.exists(tree_item.path):
            return None

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole or role >= self.Roles.FirstDataRole:
            return self._file_data(tree_item.path, role, field)
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
                self.Roles.DisplaySizeRole: lambda: self._size_string(
                    file_info
                ),
                self.Roles.DisplayLastModifiedRole: lambda: self._date_string(
                    file_info
                ),
            }
        )
        data = switch.get(field, lambda: None)()
        return str(data) if role == Qt.DisplayRole else data

    def roleNames(self):
        return self._role_names

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, _section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        return self._role_names.get(role, '').title()

    def _get_item(self, index):
        if index and index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self._root_item

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self._get_item(parent)
        try:
            child_item = parent_item.children[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, child_item)

    def parent(self, index=QModelIndex()):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self._root_item:
            return QModelIndex()

        try:
            row = parent_item.row
        except RecursionError:
            return QModelIndex()
        return self.createIndex(row, 0, parent_item)

    def columnCount(self, _parent=QModelIndex()):
        return len(self._role_names)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        parent_item = (
            parent.internalPointer() if parent.isValid() else self._root_item
        )
        return len(parent_item.children) if parent_item else 0

    @staticmethod
    def _date_string(fi):
        last_modified = fi.lastModified()
        if QDate.currentDate() == last_modified.date():
            return last_modified.time().toString(Qt.DefaultLocaleShortDate)
        else:
            return last_modified.date().toString(Qt.DefaultLocaleShortDate)

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
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}B"
            num /= 1024.0
        return "{:.1f}{}B".format(num, 'Yi')

    @staticmethod
    def _size(fi):
        if fi.isDir():
            return len(os.listdir(fi.filePath()))
        else:
            return fi.size()

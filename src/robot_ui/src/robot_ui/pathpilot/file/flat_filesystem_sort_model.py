from fnmatch import fnmatch

from PySide6.QtCore import (
    Qt,
    QRegularExpression,
    Property,
    Signal,
)
from PySide6.QtQml import QmlElement

from ..models.sort_filter_proxy_model import (
    SortFilterProxyModel,
)
from .flat_filesystem_model import FlatFileSystemModel

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FlatFileSystemSortModel(SortFilterProxyModel):
    filterChanged = Signal(str)
    nameFiltersChanged = Signal('QStringList')
    filterDirsChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._source = None
        self._name_filters = []
        self._filter_dirs = False
        self._fields = [
            FlatFileSystemModel.Roles.FileNameRole,
            FlatFileSystemModel.Roles.SizeRole,
            FlatFileSystemModel.Roles.LastModifiedRole,
        ]

        self.setFilterRole(FlatFileSystemModel.Roles.FileNameRole)

    def lessThan(self, left, right):
        left_is_dir = bool(
            self.sourceModel().data(left, FlatFileSystemModel.Roles.IsDirRole)
        )
        right_is_dir = bool(
            self.sourceModel().data(right, FlatFileSystemModel.Roles.IsDirRole)
        )
        if left_is_dir is not right_is_dir:
            if self.sortOrder() == Qt.AscendingOrder:
                return left_is_dir > right_is_dir
            else:
                return left_is_dir < right_is_dir

        return super().lessThan(left, right)

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        is_dir = self.sourceModel().data(
            index, FlatFileSystemModel.Roles.IsDirRole
        )
        filename = self.sourceModel().data(
            index, FlatFileSystemModel.Roles.FileNameRole
        )
        if is_dir is None or filename is None:
            return False

        filtered = False
        if not (
            not self.filterRegularExpression().isValid()
            or (is_dir and not self._filter_dirs)
        ):
            filtered = (
                not self.filterRegularExpression().match(filename).hasMatch()
            )
        for wildcard in self._name_filters:
            if fnmatch(filename, wildcard):
                filtered = True
                break
        return not filtered

    @Property(str, notify=filterChanged)
    def filter(self):
        return self.filterRegularExpression().pattern()

    @filter.setter
    def filter(self, value):
        self.setFilterRegularExpression(
            QRegularExpression(value, QRegularExpression.CaseInsensitiveOption)
        )
        self.filterChanged.emit(value)

    @Property(bool, notify=filterDirsChanged)
    def filterDirs(self):
        return self._filterDirs

    @filterDirs.setter
    def filterDirs(self, value):
        if value == self._filter_dirs:
            return
        self._filter_dirs = value
        self.filterDirsChanged.emit(value)

    @Property('QStringList', notify=nameFiltersChanged)
    def nameFilters(self):
        return self._name_filters

    @nameFilters.setter
    def nameFilters(self, value):
        if (
            self._name_filters == value
        ):  # note: we compare the reference here, not the actual list
            return
        self._name_filters = value
        self.nameFiltersChanged.emit(value)

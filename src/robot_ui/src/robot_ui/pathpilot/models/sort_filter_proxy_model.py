import rospy
from PySide6.QtCore import (
    QSortFilterProxyModel,
    Qt,
    Slot,
    QObject,
    Property,
    QModelIndex,
    Signal,
)
from PySide6.QtQml import QJSValue, QmlElement
from PySide6.QtGui import QFont, QFontMetrics, QGuiApplication

from ..qt_helpers import MultiSlot

QML_IMPORT_NAME = 'pathpilot.models'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class SortFilterProxyModel(QSortFilterProxyModel):
    sourceChanged = Signal()
    fieldsChanged = Signal()
    columnWidthOverridesChanged = Signal()
    headerTitlesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fields = []
        self._column_widths = {}
        self._column_width_overrides = {}
        self._header_titles = {}

    @Property(QObject, notify=sourceChanged)  # QAbstractItemModel
    def source(self):
        return self.sourceModel()

    @source.setter
    def source(self, source):
        if source is self.sourceModel():
            return

        self.setSourceModel(source)
        if self.sourceModel() is not None:
            self.setSortRole(self.sourceModel().Roles.SortRole)
        self.sourceChanged.emit()

    @Property(list, notify=fieldsChanged)
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, value):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        if value == self._fields:
            return
        self._reset_fields(value)

    @Property('QVariant', notify=columnWidthOverridesChanged)
    def columnWidthOverrides(self):
        return self._column_width_overrides

    @columnWidthOverrides.setter
    def columnWidthOverrides(self, value):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        if value == self._column_width_overrides:
            return
        self._column_width_overrides = value
        self.columnWidthOverridesChanged.emit()

    @Property('QVariant', notify=headerTitlesChanged)
    def headerTitles(self):
        return self._header_titles

    @headerTitles.setter
    def headerTitles(self, value):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        if value == self._header_titles:
            return
        self._header_titles = value
        self.headerTitlesChanged.emit()
        self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount())

    def _reset_fields(self, fields):
        self.beginResetModel()
        self._fields = fields
        self.endResetModel()
        self.fieldsChanged.emit()

    def columnCount(self, _parent=None):
        return len(self._fields)

    @MultiSlot(int, [None, int])
    def sort(self, column, order=Qt.AscendingOrder):
        column = self._role_to_source_column(self._fields[column])
        QSortFilterProxyModel.sort(self, column, Qt.SortOrder(order))

    @Slot(int, result=int)
    def initialSortOrder(self, column):
        if column < 0 or column >= len(self._fields):
            return Qt.AscendingOrder
        order = self.sourceModel().data(
            self.sourceModel().index(
                0, self._role_to_source_column(self._fields[column])
            ),
            Qt.InitialSortOrderRole,
        )
        return order or Qt.AscendingOrder

    def _role_to_source_column(self, role):
        return role - self.sourceModel().Roles.FirstDataRole - 1

    def _source_column_to_role(self, column):
        return self.sourceModel().Roles.FirstDataRole + column + 1

    def mapFromSource(self, source_index):
        row = QSortFilterProxyModel.mapFromSource(self, source_index).row()
        field = self._source_column_to_role(source_index.column())
        try:
            column = self._fields.index(field)
        except ValueError:
            column = source_index.column()
        return self.sourceModel().index(row, column)

    def mapToSource(self, proxy_index):
        if proxy_index.model() is not None and proxy_index.model() is not self:
            return QModelIndex()  # workaround for wrong indexes passed
        row_index = QSortFilterProxyModel.mapToSource(self, proxy_index)
        column = -1
        if 0 <= proxy_index.column() < len(self._fields):
            column = self._role_to_source_column(
                self._fields[proxy_index.column()]
            )
        return self.sourceModel().index(row_index.row(), column)

    @MultiSlot(int, [None, QFont], result=int)
    def columnWidth(self, column, font=None):
        if column < 0 or column >= len(self._fields):
            return 0
        source_column = self._role_to_source_column(self._fields[column])
        field = self._source_column_to_role(source_column)
        field_name = str(
            self.sourceModel().roleNames().get(field, b''), 'utf-8'
        )

        if field_name in self._column_width_overrides:
            return int(self._column_width_overrides[field_name])

        if field_name not in self._column_widths:
            fm = (
                QFontMetrics(QGuiApplication.font())
                if font is None
                else QFontMetrics(font)
            )
            width = fm.horizontalAdvance(self.headerData(column, Qt.Horizontal))
            for i in range(self.rowCount()):
                string = self.data(self.index(i, column), Qt.DisplayRole)
                width = max(width, fm.horizontalAdvance(string))
            self._column_widths[field_name] = width
        return self._column_widths[field_name]

    @MultiSlot(int, int, [None, QFont], result=int)
    def rowHeight(self, row, role, font=None):
        column = self._fields.index(role)
        fm = (
            QFontMetrics(QGuiApplication.font())
            if font is None
            else QFontMetrics(font)
        )
        string = self.data(self.index(row, column), Qt.DisplayRole)
        n_lines = string.count('\n') + 1
        return fm.lineSpacing() * n_lines

    @Slot(int, int, list)
    def reorderColumn(self, col, x, column_widths):
        column_widths = (
            column_widths.toVariant()
            if isinstance(column_widths, QJSValue)
            else column_widths
        )
        if len(column_widths) < len(self._fields):
            rospy.logerr("Not enough column widths provided.")
            return
        xc = 0
        dest_col = 0
        while xc < x and dest_col < len(self._fields):
            xc += column_widths[dest_col]
            dest_col += 1
        dest_col -= 1
        if col == dest_col:
            return
        if col > dest_col:
            dest_col, col = col, dest_col
        if not self.beginMoveColumns(
            QModelIndex(), col, col, QModelIndex(), dest_col + 1
        ):
            rospy.logerr(f"Cannot move column {col} to {dest_col}.")
        self._fields.insert(dest_col, self._fields.pop(col))
        self.endMoveColumns()
        self.fieldsChanged.emit()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return ""

        section = self._role_to_source_column(self._fields[section])
        field = self._source_column_to_role(section)
        field_name = str(
            self.sourceModel().roleNames().get(field, b''), 'utf-8'
        )
        if field_name in self._header_titles:
            return self._header_titles[field_name]
        else:
            return field_name.title()

from enum import IntEnum, auto
from PySide6.QtCore import (
    QByteArray,
    Qt,
    QEnum,
    Signal,
    Property,
    QModelIndex,
)
from PySide6.QtQml import QJSValue, QmlElement

from ..models.base_table_model import (
    BaseTableModel,
)

QML_IMPORT_NAME = 'pathpilot.development'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class DummyTableModel(BaseTableModel):
    class Roles(IntEnum):
        SortRole = Qt.UserRole
        TypeRole = auto()
        FirstDataRole = auto()  # here begins the data field roles
        NameRole = auto()
        AgeRole = auto()
        PhoneRole = auto()
        LastDataRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.SortRole: QByteArray(b'sort'),
        Roles.TypeRole: QByteArray(b'type'),
        Roles.NameRole: QByteArray(b'name'),
        Roles.AgeRole: QByteArray(b'age'),
        Roles.PhoneRole: QByteArray(b'phone'),
    }

    inputDataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._role_names.update(self._ROLE_NAMES)

        self._input_data = []

    @Property(QJSValue, notify=inputDataChanged)
    def inputData(self):
        return self._input_data

    @inputData.setter
    def inputData(self, value):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        if value == self._input_data:
            return
        self.beginResetModel()
        self._input_data = value
        self.inputDataChanged.emit()
        self.endResetModel()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role < self.Roles.FirstDataRole:
            field = self.Roles.FirstDataRole + index.column() + 1
        else:
            field = role

        if role == Qt.DisplayRole:
            return str(self.data(index, field))
        elif role >= self.Roles.FirstDataRole:
            item = index.internalPointer()
            switch = {
                self.Roles.NameRole: lambda: item.get('name', ""),
                self.Roles.AgeRole: lambda: item.get('age', 0),
                self.Roles.PhoneRole: lambda: item.get('phone', 0),
            }
            return switch.get(role, lambda: None)()
        elif role == Qt.InitialSortOrderRole:
            return Qt.AscendingOrder
        elif role == self.Roles.SortRole:
            return self.data(index, field)
        elif role == self.Roles.TypeRole:
            return self._role_names.get(field, None)
        else:
            return None

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._input_data)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._input_data[row]
        except (IndexError, AttributeError):
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

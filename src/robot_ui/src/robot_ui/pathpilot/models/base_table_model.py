from PySide6.QtCore import (
    QAbstractItemModel,
    Qt,
    QModelIndex,
)


class BaseTableModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._role_names = QAbstractItemModel.roleNames(self)

    def roleNames(self):
        return self._role_names

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, _index):
        return QModelIndex()

    def columnCount(self, _parent=None):
        return self.Roles.LastDataRole - self.Roles.FirstDataRole - 1

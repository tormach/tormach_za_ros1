from PySide6.QtCore import (
    QSortFilterProxyModel,
    QAbstractItemModel,
    Property,
)
from PySide6.QtQml import QmlElement

from robot_ui.pathpilot.robot.machinetalk import MachinetalkInstanceListModel

QML_IMPORT_NAME = 'pathpilot.plugins.pathpilot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


# based on: https://stackoverflow.com/questions/20969261/how-to-sort-qml-tableview-in-qtquick-2
@QmlElement
class FilteredInstanceModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._source = None

    @Property(QAbstractItemModel)
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self.setSourceModel(source)
        self._source = source

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        selected = self.sourceModel().data(
            index, MachinetalkInstanceListModel.Roles.SelectedRole
        )
        return selected

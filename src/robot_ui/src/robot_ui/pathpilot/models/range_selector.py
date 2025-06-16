from PySide6.QtCore import (
    QObject,
    QItemSelectionModel,
    QModelIndex,
    QItemSelection,
    Property,
    Signal,
    Slot,
)
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.models'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class RangeSelector(QObject):
    modelChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None

    @Property(QObject, notify=modelChanged)  # QItemSelectionModel
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if value == self._model:
            return
        self._model = value
        self.modelChanged.emit()

    @Slot(QModelIndex, QModelIndex, int)
    def selectRange(self, from_, to, command):
        if self._model is None:
            return
        selection = QItemSelection(from_, to)
        self._model.select(
            selection, QItemSelectionModel.SelectionFlags(command)
        )

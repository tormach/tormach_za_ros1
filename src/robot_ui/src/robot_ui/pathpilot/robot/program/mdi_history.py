from PySide6.QtCore import QObject, Property, Slot, Signal
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class MdiHistory(QObject):
    currentCommandChanged = Signal()
    maximumCountChanged = Signal(int)
    mdiHistoryChanged = Signal()

    def __init__(self, parent=None, maximum_count=10, mdi_history=None):
        super().__init__(parent)

        if mdi_history is None:
            mdi_history = []
        self._maximum_count = maximum_count
        self._current_index = -1
        self._mdi_history = mdi_history

        self.mdiHistoryChanged.connect(self._update_current_command)

    @Property(int, notify=maximumCountChanged)
    def maximumCount(self):
        return self._maximum_count

    @maximumCount.setter
    def maximumCount(self, value):
        if value == self._maximum_count:
            return

        self._maximum_count = value
        self.maximumCountChanged.emit(value)

    @Property('QStringList', notify=mdiHistoryChanged)
    def mdiHistory(self):
        return self._mdi_history

    @mdiHistory.setter
    def mdiHistory(self, value):
        if (
            value == self._mdi_history
        ):  # note: we compare the reference here, not the actual list
            return
        self._mdi_history = value
        self.mdiHistoryChanged.emit()

    @Property(str, notify=currentCommandChanged)
    def currentCommand(self):
        if self._current_index > -1:
            return self._mdi_history[self._current_index]
        else:
            return ""

    @Slot()
    def nextCommand(self):
        if len(self._mdi_history) == 0:
            return

        if self._current_index < len(self._mdi_history) - 1:
            self._current_index += 1
        else:
            self._current_index = 0
        self.currentCommandChanged.emit()

    @Slot()
    def previousCommand(self):
        if len(self._mdi_history) == 0:
            return

        if self._current_index > 0:
            self._current_index -= 1
        else:
            self._current_index = len(self._mdi_history) - 1
        self.currentCommandChanged.emit()

    @Slot(str)
    def appendCommand(self, value):
        if value == "":
            return
        if value in self._mdi_history:
            self._mdi_history.remove(value)
        self._mdi_history.append(value)
        if len(self._mdi_history) > self._maximum_count:
            self._mdi_history.pop(0)

        self.mdiHistoryChanged.emit()

    @Slot()
    def clear(self):
        del self._mdi_history[:]
        self.mdiHistoryChanged.emit()

    @Slot()
    def _update_current_command(self):
        self._current_index = -1
        self.currentCommandChanged.emit()

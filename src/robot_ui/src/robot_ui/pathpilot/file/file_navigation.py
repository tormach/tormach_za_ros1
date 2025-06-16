import os

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FileNavigation(QObject):
    absoluteChanged = Signal(bool)
    homePathChanged = Signal(str)
    currentPathChanged = Signal(str)

    def __init__(
        self, parent=None, home_path='', current_path='', absolute=True
    ):
        super().__init__(parent)

        self._absolute = absolute
        self._set_home_path = home_path
        self._home_path = self._expand_path(home_path)
        self._set_current_path = current_path
        self._current_path = self._expand_path(current_path)

        self.absoluteChanged.connect(self._update_abs_path)

    @Property(bool, notify=absoluteChanged)
    def absolute(self):
        return self._absolute

    @absolute.setter
    def absolute(self, value):
        if value == self._absolute:
            return
        self._absolute = value
        self.absoluteChanged.emit(value)

    @Property(str, notify=homePathChanged)
    def homePath(self):
        return self._home_path

    @homePath.setter
    def homePath(self, value):
        abs_path = self._expand_path(value)
        if abs_path == self._home_path:
            return
        self._set_home_path = value
        self._home_path = abs_path
        self.homePathChanged.emit(abs_path)

    @Property(str, notify=currentPathChanged)
    def currentPath(self):
        return self._current_path

    @currentPath.setter
    def currentPath(self, value):
        abs_path = self._expand_path(value)
        if abs_path == self._current_path:
            return
        self._set_current_path = value
        self._current_path = abs_path
        self.currentPathChanged.emit(abs_path)

    @Slot()
    def navigateHome(self):
        self.currentPath = self._home_path

    @Slot()
    def navigateBack(self):
        if self._current_path == self._home_path:
            return
        parent = os.path.dirname(self._current_path)
        self.currentPath = parent

    def _expand_path(self, path):
        if not path:
            return ''
        if self._absolute:
            return os.path.realpath(os.path.expanduser(path))
        else:
            return path

    @Slot()
    def _update_abs_path(self):
        self.homePath = self._set_home_path
        self.currentPath = self._set_current_path

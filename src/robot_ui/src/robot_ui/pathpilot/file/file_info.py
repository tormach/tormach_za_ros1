import os

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FileInfo(QObject):
    """Shows information about a file."""

    pathChanged = Signal(str)
    existsChanged = Signal(bool)
    isFileChanged = Signal(bool)
    absolutePathChanged = Signal(str)

    def __init__(self, parent=None, path=''):
        super().__init__(parent)

        self._path = path
        self._is_file = False
        self._exists = False
        self._absolute_path = ''
        self._update()

        self.pathChanged.connect(self._update)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(str, notify=absolutePathChanged)
    def absolutePath(self):
        return self._absolute_path

    @Property(bool, notify=isFileChanged)
    def isFile(self):
        return self._is_file

    @Property(bool, notify=existsChanged)
    def exists(self):
        return self._exists

    @Slot()
    def _update(self):
        self._absolute_path = os.path.abspath(os.path.expanduser(self._path))
        self._exists = os.path.exists(self._absolute_path)
        self._is_file = os.path.isfile(self._absolute_path)

        self.absolutePathChanged.emit(self._absolute_path)
        self.existsChanged.emit(self._exists)
        self.isFileChanged.emit(self._is_file)

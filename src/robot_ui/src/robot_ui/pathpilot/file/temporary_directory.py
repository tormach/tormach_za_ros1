import os
from shutil import rmtree
from tempfile import mkdtemp

from PySide6.QtCore import QObject, Property, Slot, Signal
from PySide6.QtQml import QmlElement

from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class TemporaryDirectory(QObject):
    pathChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._path = ''
        self._create_directory()

        ensure_cleanup(self.remove)

    def _create_directory(self):
        self._path = mkdtemp(prefix='robot_programs_')
        self.pathChanged.emit(self._path)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @Slot()
    def cleanup(self, destroy=False):
        rmtree(self._path, ignore_errors=True)
        if not destroy:
            self._create_directory()

    @Slot()
    def remove(self):
        self.cleanup(destroy=True)

    @Slot(str, result=str)
    def createFilePath(self, name):
        return os.path.join(self._path, name)

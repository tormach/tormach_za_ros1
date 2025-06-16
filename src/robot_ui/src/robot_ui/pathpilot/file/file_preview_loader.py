import os

from PySide6.QtCore import (
    QObject,
    QMimeDatabase,
    Signal,
    Property,
    Slot,
)
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FilePreviewLoader(QObject):
    """
    This class verifies if a file is previewable and loads the file contents if it is.
    """

    pathChanged = Signal(str)
    previewableChanged = Signal(bool)
    contentChanged = Signal()
    sizeLimitChanged = Signal(int)

    def __init__(self, parent=None, path='', size_limit=None):
        super().__init__(parent)

        self._path = path
        self._previewable = False
        self._content = ''
        self._size_limit = (
            (1024 * 1024 * 2) if not size_limit else size_limit
        )  # 2MiB
        self._mime_db = QMimeDatabase()

        self.pathChanged.connect(self._update_file)
        self.sizeLimitChanged.connect(self._update_file)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(bool, notify=previewableChanged)
    def previewable(self):
        return self._previewable

    @Property(str, notify=contentChanged)
    def content(self):
        return self._content

    @Property(int, notify=sizeLimitChanged)
    def sizeLimit(self):
        return self._size_limit

    @sizeLimit.setter
    def sizeLimit(self, value):
        if value == self._size_limit:
            return
        self._size_limit = value
        self.sizeLimitChanged.emit(value)

    def _check_file_previewable(self, path, size_limit):
        if not os.path.exists(path):
            return False

        type_ = self._mime_db.mimeTypeForFile(path)
        if not type_.isValid():
            return False
        if not type_.name().startswith('text'):
            return False

        return os.path.getsize(path) <= size_limit

    @Slot()
    def _update_file(self):
        self._previewable = self._check_file_previewable(
            self._path, self._size_limit
        )

        if self._previewable:
            with open(self._path) as f:
                self._content = f.read()
        else:
            self._content = ''

        self.previewableChanged.emit(self._previewable)
        self.contentChanged.emit()

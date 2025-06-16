import os

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from .file_utils import get_files_from_qml_data

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FileSelection(QObject):
    """
    Shows information for a list of selected files.
    """

    pathChanged = Signal(str)
    filesChanged = Signal()
    fileCountChanged = Signal(int)
    folderCountChanged = Signal(int)
    programSelectedChanged = Signal()
    programPathChanged = Signal()

    def __init__(self, parent=None, path=''):
        super().__init__(parent)

        self._path = path
        self._files = []
        self._file_count = 0
        self._folder_count = 0

        self.pathChanged.connect(self._update_file_metrics)
        self.filesChanged.connect(self._update_file_metrics)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(list, notify=filesChanged)
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        if value == self._files:
            return
        self._files = value
        self.filesChanged.emit()

    @Property(int, notify=fileCountChanged)
    def fileCount(self):
        return self._file_count

    @Property(int, notify=folderCountChanged)
    def folderCount(self):
        return self._folder_count

    @Property(bool, notify=programSelectedChanged)
    def programSelected(self):
        return self._file_count == 1 and self._folder_count == 0

    @Property(str, notify=programPathChanged)
    def programPath(self):
        files = get_files_from_qml_data(self._files)
        if len(files) != 1 or not files[0]:
            return ""
        abs_path = os.path.abspath(os.path.expanduser(self._path))
        return os.path.join(abs_path, files[0])

    @staticmethod
    def listdir(fullpath):
        return os.listdir(fullpath)

    @staticmethod
    def isdir(fullpath):
        return os.path.isdir(fullpath)

    @Slot()
    def _update_file_metrics(self):
        """
        Updates the number of files and folders in the current selection.
        """
        path = os.path.abspath(os.path.expanduser(self._path))
        items = get_files_from_qml_data(self._files)

        if os.path.exists(path):
            files, folders = 0, 0
            for item in items:
                if not item:  # invalid selection
                    continue
                file_path = os.path.join(path, item)
                item_files, item_folders = self._count_files_and_folders(
                    file_path
                )
                files += item_files
                folders += item_folders
        else:
            files = 0
            folders = 0

        self._folder_count = folders
        self._file_count = files
        self.folderCountChanged.emit(folders)
        self.fileCountChanged.emit(files)
        self.programSelectedChanged.emit()
        self.programPathChanged.emit()

    @staticmethod
    def _count_files_and_folders(path):
        """
        :returns the number of files and folders as a tuple
        :type path: str
        :rtype: tuple
        """
        if os.path.isfile(path):
            return 1, 0

        n_files = 0
        n_folders = 1
        for _, dirs, files in os.walk(path, followlinks=True):
            n_files += sum(1 for _ in files)
            n_folders += sum(1 for _ in dirs)
        return n_files, n_folders

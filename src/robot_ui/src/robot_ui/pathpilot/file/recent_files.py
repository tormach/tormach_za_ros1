import logging
import os

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement

logger = logging.getLogger(__name__)


QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class RecentFiles(QObject):
    """
    Captures and stores recently used files and paths.
    """

    currentPathChanged = Signal(str)
    recentPathsChanged = Signal()
    maximumCountChanged = Signal(int)
    recentFilesChanged = Signal()
    homePathChanged = Signal(str)

    def __init__(
        self,
        parent=None,
        current_path='',
        storage_path='',
        recent_paths=None,
        maximum_count=10,
        home_path='',
    ):
        super().__init__(parent)

        if recent_paths is None:
            recent_paths = []
        self._current_path = current_path
        self._storage_path = storage_path
        self._recent_paths = recent_paths
        self._maximum_count = maximum_count
        self._home_path = home_path

        self.currentPathChanged.connect(self._update_current_path)
        self.recentPathsChanged.connect(self.recentFilesChanged)

    @Property(str, notify=currentPathChanged)
    def currentPath(self):
        return self._current_path

    @currentPath.setter
    def currentPath(self, value):
        value = os.path.expanduser(value)
        if value == self._current_path:
            return
        self._current_path = value
        self.currentPathChanged.emit(value)

    @Property('QStringList', notify=recentPathsChanged)
    def recentPaths(self):
        """
        Returns a list of recent paths. The last item is also the most recently used one.
        """
        return self._recent_paths

    @recentPaths.setter
    def recentPaths(self, value):
        if (
            self._recent_paths == value
        ):  # note: we compare the reference here, not the actual list
            return
        self._recent_paths = [p for p in value if os.path.exists(p)]
        self.recentPathsChanged.emit()

    @Property('QStringList', notify=recentFilesChanged)
    def recentFiles(self):
        """
        Returns the file names of the most recent paths. The last item is also the most recently used one.
        """
        return [os.path.basename(path) for path in self._recent_paths]

    @Property(int, notify=maximumCountChanged)
    def maximumCount(self):
        return self._maximum_count

    @maximumCount.setter
    def maximumCount(self, value):
        if value == self._maximum_count:
            return
        self._maximum_count = value
        self.maximumCountChanged.emit(value)

    @Property(str, notify=homePathChanged)
    def homePath(self):
        return self._home_path

    @homePath.setter
    def homePath(self, value):
        value = os.path.expanduser(value)
        if value == self._home_path:
            return
        self._home_path = value
        self.homePathChanged.emit(value)

    @Slot()
    def clear(self):
        del self._recent_paths[:]
        self.recentPathsChanged.emit()

    @Slot()
    def _update_current_path(self):
        # ignore empty paths and paths outside of the home directory
        if self._current_path == '':
            return
        if not self._current_path.startswith(self._home_path):
            return

        # append item to the end of the list if not already there
        changed = False
        try:
            index = self._recent_paths.index(self._current_path)
            if index == len(self._recent_paths) - 1:
                changed = False
            else:
                del self._recent_paths[index]
                changed = True
        except ValueError:
            changed = True

        if changed:
            self._recent_paths.append(self._current_path)

        # trim list to maximum size
        if len(self._recent_paths) > self._maximum_count:
            self._recent_paths = self._recent_paths[-self._maximum_count :]
            changed = True

        # only emit signal if list has changed
        if changed:
            self.recentPathsChanged.emit()

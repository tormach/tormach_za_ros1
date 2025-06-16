import os
import contextlib
from fnmatch import fnmatch
from inotify_simple import INotify, flags

from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
    QUrl,
    QDirIterator,
    QTimer,
    qWarning,
)
from PySide6.QtQml import QmlElement

from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FileWatcher(QObject):
    fileUrlChanged = Signal(QUrl)
    enabledChanged = Signal(bool)
    recursiveChanged = Signal(bool)
    nameFiltersChanged = Signal()
    fileChanged = Signal()

    CHECK_INTERVAL_MS = 100
    FLAGS = (
        flags.CREATE
        | flags.MODIFY
        | flags.DELETE
        | flags.MOVED_FROM
        | flags.MOVED_TO
        | flags.ATTRIB
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        self._file_url = QUrl()
        self._enabled = True
        self._recursive = False
        self._name_filters = []
        self._watched_paths = set()
        self._error_string = ""
        self._inotify = None
        self._check_timer = None

        try:
            self._inotify = INotify(nonblocking=True)
        except OSError as e:
            self._error_string = str(e)
            qWarning(self.tr("Failed to initialize FileWatcher: {0}").format(e))
            return

        self._check_timer = QTimer(self)
        self._check_timer.setInterval(self.CHECK_INTERVAL_MS)
        self._check_timer.timeout.connect(self._check_events)
        self._check_timer.start()

        self.fileUrlChanged.connect(self._update_watched_file)
        self.enabledChanged.connect(self._update_watched_file)
        self.recursiveChanged.connect(self._update_watched_file)
        self.nameFiltersChanged.connect(self._update_watched_file)
        ensure_cleanup(self._on_destroyed)

    @Property(QUrl, notify=fileUrlChanged)
    def fileUrl(self):
        return self._file_url

    @fileUrl.setter
    def fileUrl(self, value):
        if self._file_url == value:
            return
        self._file_url = value
        self.fileUrlChanged.emit(value)

    @Property(bool, notify=enabledChanged)
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._enabled == value:
            return
        self._enabled = value
        self.enabledChanged.emit(value)

    @Property(bool, notify=recursiveChanged)
    def recursive(self):
        return self._recursive

    @recursive.setter
    def recursive(self, value):
        if self._recursive == value:
            return
        self._recursive = value
        self.recursiveChanged.emit(value)

    @Property('QStringList', notify=nameFiltersChanged)
    def nameFilters(self):
        return self._name_filters

    @nameFilters.setter
    def nameFilters(self, value):
        if self._name_filters == value:
            return
        self._name_filters = value
        self.nameFiltersChanged.emit()

    @Property(bool, constant=True)
    def hasError(self):
        return self._inotify is None

    @Property(str, constant=True)
    def errorString(self):
        return self._error_string

    @Slot()
    def _update_watched_file(self):
        for wd in self._watched_paths:
            with contextlib.suppress(OSError):
                self._inotify.rm_watch(wd)

        self._watched_paths.clear()

        if not self._file_url.isValid() or not self._enabled:
            return False

        if not self._file_url.isLocalFile():
            qWarning('Can only watch local files')
            return False

        local_file = self._file_url.toLocalFile()
        if local_file == '':
            return False

        if os.path.isdir(local_file):
            changed, self._watched_paths = self._update_watched_directory(
                local_file, self._watched_paths
            )
            return changed

        elif os.path.exists(local_file):
            wd = self._inotify.add_watch(local_file, self.FLAGS)
            self._watched_paths.add(wd)
            return True

        else:
            qWarning('File to watch does not exist')
            return False

    def _update_watched_directory(self, local_file, watched_paths):
        new_paths = {self._inotify.add_watch(local_file, self.FLAGS)}

        options = QDirIterator.FollowSymlinks
        if self._recursive:
            options |= QDirIterator.Subdirectories
        it = QDirIterator(local_file, options)
        while it.hasNext():
            filepath = it.next()
            filename = os.path.basename(filepath)
            filtered = any(
                fnmatch(filename, wildcard) for wildcard in self._name_filters
            )
            if filename == '..' or filename == '.' or filtered:
                continue
            wd = self._inotify.add_watch(filepath, self.FLAGS)
            new_paths.add(wd)

        return new_paths != watched_paths, new_paths

    @Slot()
    def _check_events(self):
        if not self._enabled:
            _ = self._inotify.read(timeout=0)  # discard events
            return
        changed = False
        for event in list(self._inotify.read(timeout=0)):
            if not event.mask & self.FLAGS:
                continue
            filtered = any(
                fnmatch(event.name, wildcard) for wildcard in self._name_filters
            )
            if filtered:
                continue
            changed = True
            break

        if changed:
            self.fileChanged.emit()

    @Slot()
    def _on_destroyed(self):
        if self._inotify:
            self._inotify.close()
            self._inotify = None
        if self._check_timer:
            self._check_timer.stop()
            self._check_timer = None
            self._check_timer = None

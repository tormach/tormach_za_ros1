import os
import contextlib
from subprocess import check_call, CalledProcessError

import rospy
import time
from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
    qWarning,
    QTimer,
)
from PySide6.QtQml import QmlElement
from inotify_simple import INotify, flags

from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class UsbMediaWatcher(QObject):
    _MAX_PERMISSION_WAIT_TIMEOUT_S = 0.2

    pathChanged = Signal(str)
    usbPathChanged = Signal(str)
    usbMountedChanged = Signal(bool)
    mediaNameChanged = Signal(str)

    CHECK_INTERVAL_MS = 100
    FLAGS = (
        flags.CREATE
        | flags.DELETE
        | flags.MODIFY
        | flags.MOVED_FROM
        | flags.MOVED_TO
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        self._path = ""
        self._usb_path = ""
        self._usb_mounted = False
        self._media_name = ""
        self._inotify = None
        self._check_timer = None
        self._watch_descriptor = None

        try:
            self._inotify = INotify(nonblocking=True)
        except OSError as e:
            self._error_string = str(e)
            qWarning(
                self.tr("Failed to initialize UsbMediaWatcher: {0}").format(e)
            )
            return

        self._check_timer = QTimer(self)
        self._check_timer.setInterval(self.CHECK_INTERVAL_MS)
        self._check_timer.timeout.connect(self._check_events)
        self._check_timer.start()

        self.pathChanged.connect(self._update_watched_directory)
        ensure_cleanup(self._on_destroyed)

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(str, notify=usbPathChanged)
    def usbPath(self):
        return self._usb_path

    @Property(bool, notify=usbMountedChanged)
    def usbMounted(self):
        return self._usb_mounted

    @Property(str, notify=mediaNameChanged)
    def mediaName(self):
        return self._media_name

    @Slot()
    def unmountMedia(self):
        if not self._usb_mounted:
            return
        disk_name = self._find_media_mount_disk_name(self._usb_path)
        if disk_name is None:
            rospy.logerr(
                self.tr("Could not find disk name for mount point {}").format(
                    self._usb_path
                )
            )
            return

        command = ['udisksctl', 'unmount', '--block-device', disk_name]
        try:
            check_call(command)
        except CalledProcessError as e:
            rospy.logerr(
                self.tr("Error unmounting USB device {}").format(str(e))
            )
        else:
            # unmount was successful, be quicker updating the path than inotify
            self._usb_path = ""
            self._media_name = ""
            self._usb_mounted = False
            self.usbPathChanged.emit(self._usb_path)
            self.mediaNameChanged.emit(self._media_name)
            self.usbMountedChanged.emit(self._usb_mounted)

    @staticmethod
    def _find_media_mount_disk_name(path):
        with open('/proc/mounts') as f:
            mounts = [line.split() for line in f.readlines()]
        for mount in mounts:
            mount_name = mount[1].encode().decode('unicode-escape')
            if mount_name == path:
                return mount[0]
        return None

    @Slot()
    def _update_watched_directory(self):
        if self._watch_descriptor:
            with contextlib.suppress(OSError):
                self._inotify.rm_watch(self._watch_descriptor)
            self._watch_descriptor = None

        if os.path.exists(self._path) and os.path.isdir(self._path):
            self._inotify.add_watch(self._path, self.FLAGS)

        self._update_mount_directory()

    @Slot()
    def _check_events(self):
        if self._inotify is None:
            return

        for event in list(self._inotify.read(timeout=0)):
            if not event.mask & self.FLAGS:
                continue
            self._update_mount_directory()
            break

    def _update_properties(self, usb_path, media_name, usb_mounted):
        if self._usb_path != usb_path:
            self._usb_path = usb_path
            self.usbPathChanged.emit(usb_path)
        if self._media_name != media_name:
            self._media_name = media_name
            self.mediaNameChanged.emit(media_name)
        if self._usb_mounted is not usb_mounted:
            self._usb_mounted = usb_mounted
            self.usbMountedChanged.emit(usb_mounted)

    def _update_mount_directory(self):
        usb_path = ""
        media_name = ""
        usb_mounted = False

        if not os.path.exists(self._path):
            rospy.logerr(f"USB mount folder {self._path} does not exist.")
            self._update_properties(usb_path, media_name, usb_mounted)
            return

        if not os.path.isdir(self._path):
            rospy.logerr(f"USB mount folder {self._path} is not a directory")
            self._update_properties(usb_path, media_name, usb_mounted)
            return

        if directories := [
            path
            for path in (
                os.path.join(self._path, name)
                for name in os.listdir(self._path)
            )
            if os.path.isdir(path)
        ]:
            usb_path = directories[0]
            media_name = os.path.basename(usb_path)
            usb_mounted = True

            # inotify is triggered quickly, but we may not have permission to access
            # mount yet, this loop usually settles withing a few iterations
            start_time = time.time()
            while os.path.isdir(usb_path) and (
                time.time() - start_time < self._MAX_PERMISSION_WAIT_TIMEOUT_S
            ):
                try:
                    os.listdir(usb_path)
                    break
                except PermissionError:
                    time.sleep(0.01)

        self._update_properties(usb_path, media_name, usb_mounted)

    @Slot()
    def _on_destroyed(self):
        if self._inotify:
            self._inotify.close()
            self._inotify = None
        if self._check_timer:
            self._check_timer.stop()
            self._check_timer = None

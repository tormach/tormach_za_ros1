import contextlib
import re
import subprocess

from PySide6.QtCore import (
    Signal,
    Property,
    Slot,
    QTimer,
    QRectF,
    QRect,
    QCoreApplication,
    Qt,
)
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QmlElement

import rospy

from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.controls'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WindowController(QQuickItem):
    """
    Controls the visibility and position of an external window
    to match to match this item.

    The winId property must be set to the window ID of the external window.

    The active property must be set to true to capture the window and
    false to release it.

    The captured property indicates whether the window is currently captured.
    """

    UPDATE_INTERVAL_MS = 100

    activeChanged = Signal()
    winIdChanged = Signal()
    captured = Signal()
    released = Signal()
    windowCapturedChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._active = False
        self._window = None
        self._win_id = 0
        self._last_geometry = QRect()
        self._last_visible = False
        self._last_flags = None
        self._force_update = 0
        self._active_flags = None
        self._inactive_flags = None

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(self.UPDATE_INTERVAL_MS)
        self._update_timer.timeout.connect(self._map_size_and_pos)

        self.visibleChanged.connect(self._map_size_and_pos)
        self.activeChanged.connect(self._capture_or_release_window)
        self.winIdChanged.connect(self._capture_or_release_window)
        self.captured.connect(self.windowCapturedChanged)
        self.released.connect(self.windowCapturedChanged)
        ensure_cleanup(self._on_destruction)

        self._window_manager = self._detect_window_manager()
        if self._window_manager:
            rospy.loginfo(
                self.tr(f"Detected window manager: {self._window_manager}")
            )
        else:
            rospy.logwarn(self.tr("Failed to detect window manager"))

    @staticmethod
    def _detect_window_manager():
        try:
            output = subprocess.check_output(
                ["xprop", "-root", "-notype", "_NET_SUPPORTING_WM_CHECK"]
            )
        except subprocess.CalledProcessError or FileNotFoundError:
            return None

        if "no such atom" in output.decode("utf-8"):
            return None
        prop_id = output.decode("utf-8").split(" ")[-1].strip()
        try:
            output = subprocess.check_output(
                ["xprop", "-id", prop_id, "-notype", "_NET_WM_NAME"]
            )
        except subprocess.CalledProcessError or FileNotFoundError:
            return None
        if "no such atom" in output.decode("utf-8"):
            return None
        pattern = r'_NET_WM_NAME = "(.*?)"'
        if match := re.search(pattern, output.decode("utf-8")):
            return match[1]
        return None

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        if value == self._active:
            return

        self._active = value
        self.activeChanged.emit()

    @Property(int, notify=winIdChanged)
    def winId(self):
        return self._win_id

    @winId.setter
    def winId(self, value):
        if value == self._win_id:
            return

        self._win_id = value
        self.winIdChanged.emit()

    @Property(str, constant=True)
    def windowManager(self):
        return self._window_manager or ""

    @Property(bool, notify=windowCapturedChanged)
    def windowCaptured(self):
        return self._window is not None

    def _reset_last_state(self):
        self._last_geometry = QRect()
        self._last_visible = False
        self._last_flags = None
        self._force_update = 0

    @Slot()
    def _capture_or_release_window(self):
        if self._active and self._win_id:
            self._release_window()  # release in case another window is captured
            self._capture_window()
        else:
            self._release_window()

    def _capture_window(self):
        rospy.logdebug(self.tr(f"Capturing external window {self._win_id}"))
        self._window = QWindow.fromWinId(self._win_id)
        if not self._window:
            rospy.logerr(self.tr("Failed to capture external window"))
            return
        self._reset_last_state()
        self._window.setParent(self.window())
        if self._window_manager == "Xfwm4":
            self._active_flags = Qt.SubWindow | Qt.FramelessWindowHint
            self._inactive_flags = self._active_flags
        elif self._window_manager == "KWin":
            self._active_flags = Qt.Popup | Qt.FramelessWindowHint
            self._inactive_flags = self._active_flags
        else:
            self._active_flags = Qt.Popup | Qt.FramelessWindowHint
            self._inactive_flags = Qt.Tool | Qt.FramelessWindowHint
        self._force_update = 2  # force multiple times to ensure geometry is set
        self._window.setVisible(True)  # needs to be set to true initially
        self._map_size_and_pos()
        self._update_timer.start()
        self.captured.emit()

    def _release_window(self):
        if not self._window:
            return

        rospy.logdebug(
            QCoreApplication.instance().tr("Releasing external window")
        )
        self._update_timer.stop()
        if self._win_id != 0:  # no need to modify window when app exits
            self._window.setParent(None)
            self._window.show()
        self._window = None
        with contextlib.suppress(RuntimeError):
            self.released.emit()  # may be called after destruction

    @Slot()
    def _map_size_and_pos(self):
        if not self._window:
            return
        rect = self.mapRectToScene(
            QRectF(0, 0, self.width(), self.height())
        ).toRect()
        visible = self.isVisible()
        flags = (
            self._active_flags
            if self._window.isActive()
            else self._inactive_flags
        )
        if flags is not self._last_flags and not self._force_update:
            self._force_update = 1  # flag change requires geometry update
        if (
            rect == self._last_geometry and visible is self._last_visible
        ) and not self._force_update:
            return
        self._window.setFlags(flags)
        if self._last_visible:
            self._window.setVisible(False)
        if self._force_update:
            self._window.setParent(None)
            self._window.setParent(self.window())
            self._window.setGeometry(QRect())
        self._window.setGeometry(rect)
        if visible or self._force_update:
            self._window.setVisible(visible)
        self._last_visible = visible
        self._last_flags = flags
        self._last_geometry = rect
        if self._force_update:
            self._force_update -= 1

    @Slot()
    def _on_destruction(self):
        self._update_timer.stop()
        self._release_window()

import contextlib

from PySide6.QtCore import (
    Property,
    Signal,
    Slot,
    QPointF,
    QSizeF,
    QTimer,
)
from PySide6.QtQml import QmlElement
from PySide6.QtQuick import QQuickItem, QQuickWindow

from ..qt_helpers import ensure_cleanup

SCALE_UPDATE_INTERVAL = 500

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ScaleDetection(QQuickItem):
    scaleChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._window = None
        self._scale = 1.0
        self.setWidth(1)
        self.setHeight(1)

        self.windowChanged.connect(self._update_window)
        self.widthChanged.connect(self._update_scale)
        self.heightChanged.connect(self._update_scale)

        self._timer = QTimer(self)
        self._timer.setInterval(SCALE_UPDATE_INTERVAL)
        self._timer.timeout.connect(self._update_scale)

        ensure_cleanup(self._cleanup)

    def componentComplete(self):
        super().componentComplete()
        self._timer.start()

    @Slot(QQuickWindow)
    def _update_window(self, window):
        old_window, self._window = self._window, window

        if old_window:
            with contextlib.suppress(RuntimeError):
                old_window.widthChanged.disconnect(self._update_scale)
                old_window.heightChanged.disconnect(self._update_scale)
        if window:
            window.widthChanged.connect(self._update_scale)
            window.heightChanged.connect(self._update_scale)
        self._update_scale()

    @Property(float, notify=scaleChanged)
    def scale(self):
        return self._scale

    @Slot()
    def update(self):
        self._update_scale()

    @Slot()
    def _update_scale(self):
        size = QSizeF(self.width(), self.height())
        top_left = self.mapToScene(QPointF())
        bottom_right = self.mapToScene(QPointF(size.width(), size.height()))

        try:
            scale = (bottom_right.x() - top_left.x()) / size.width()
        except ZeroDivisionError:
            scale = 1.0

        self._scale = scale
        self.scaleChanged.emit()

    @Slot()
    def _cleanup(self):
        self._timer.stop()

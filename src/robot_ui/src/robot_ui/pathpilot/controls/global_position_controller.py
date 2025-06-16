import contextlib
from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    QPointF,
    QTimer,
    QSizeF,
    Slot,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QmlElement

from .global_position_object import GlobalPositionObject
from ..qt_helpers import ensure_cleanup

SIZE_UPDATE_INTERVAL = 500
POSITION_UPDATE_INTERVAL = 30

QML_IMPORT_NAME = 'pathpilot.controls'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GlobalPositionController(QObject):
    targetChanged = Signal()
    sourceChanged = Signal()
    activeChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._target: QQuickItem = None
        self._source: GlobalPositionObject = None
        self._active = True

        self.activeChanged.connect(self._update_active)
        self.activeChanged.connect(self._update_position)
        self.activeChanged.connect(self._update_size)
        self.targetChanged.connect(self._update_active)
        self.targetChanged.connect(self._update_position)
        self.targetChanged.connect(self._update_size)
        self.sourceChanged.connect(self._update_position)
        self.sourceChanged.connect(self._update_size)

        self._pos_timer = QTimer(self)
        self._pos_timer.setInterval(POSITION_UPDATE_INTERVAL)
        self._pos_timer.timeout.connect(self._update_position)
        self._size_timer = QTimer(self)
        self._size_timer.setInterval(SIZE_UPDATE_INTERVAL)
        self._size_timer.timeout.connect(self._update_size)

        ensure_cleanup(self._on_destruction)

    @Property(GlobalPositionObject, notify=targetChanged)
    def target(self):
        return self._target

    @target.setter
    def target(self, new_target):
        if new_target == self._target:
            return
        if self._target:
            with contextlib.suppress(RuntimeError):
                self._target.destroyed.disconnect(self._disconnect_target)
        if new_target:
            new_target.destroyed.connect(lambda: self._disconnect_target())
        self._target = new_target
        self.targetChanged.emit()

    def _disconnect_target(self):
        self._target = None

    @Property(QQuickItem, notify=sourceChanged)
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if value == self._source:
            return

        if self._source:
            self._disconnect_source_signals()
            self._pos_timer.stop()
            self._size_timer.stop()

        self._source = value
        self.sourceChanged.emit()

        self._connect_source_signals()
        self._pos_timer.start()
        self._size_timer.start()

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        if value == self._active:
            return
        self._active = value
        self.activeChanged.emit(value)

    @Slot()
    def _on_destruction(self):
        self._active = False
        self._pos_timer.stop()
        self._size_timer.stop()
        with contextlib.suppress(RuntimeError):
            self._update_active()

    @Slot()
    def _update_active(self):
        if not self._target:
            return
        self._target.update_controller_active(self, self._active)

    @Slot()
    def _update_position(self):
        if not (self._target and self._source and self._active):
            return
        global_pos = self._source.mapToScene(QPointF())
        self._target.set_pos(global_pos, self)

    @Slot()
    def _update_size(self):
        if not (self._target and self._source and self._active):
            return
        size = QSizeF(self._source.width(), self._source.height())

        top_left = self._source.mapToScene(QPointF())
        bottom_right = self._source.mapToScene(
            QPointF(size.width(), size.height())
        )
        try:
            scale = (bottom_right.x() - top_left.x()) / size.width()
        except ZeroDivisionError:
            scale = 1.0

        self._target.set_size(size, scale, self)

    def _connect_source_signals(self):
        if not self._source:
            return
        self._source.xChanged.connect(self._update_position)
        self._source.yChanged.connect(self._update_position)
        self._source.widthChanged.connect(self._update_size)
        self._source.heightChanged.connect(self._update_size)

    def _disconnect_source_signals(self):
        if not self._source:
            return
        with contextlib.suppress(RuntimeError):
            self._source.xChanged.disconnect(self._update_position)
            self._source.yChanged.disconnect(self._update_position)
            self._source.widthChanged.disconnect(self._update_size)
            self._source.heightChanged.disconnect(self._update_size)

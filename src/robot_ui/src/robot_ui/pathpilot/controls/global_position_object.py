from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    Slot,
    QPointF,
    QRectF,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.controls'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GlobalPositionObject(QObject):
    targetChanged = Signal()
    activeChanged = Signal(bool)
    scaleChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._target = None
        self._active_controllers = []
        self._cached_pos = {}
        self._cached_size = {}
        self._cached_scale = {}
        self._scale = 1.0

        self.targetChanged.connect(self._update_visibility)
        self.targetChanged.connect(self._apply_cached_values)

    @Property(QQuickItem, notify=targetChanged)
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if value == self._target:
            return
        self._target = value
        self.targetChanged.emit()

    @Property(bool, notify=activeChanged)
    def active(self):
        return any(self._active_controllers)

    @Property(float, notify=scaleChanged)
    def scale(self):
        return self._scale

    def set_pos(self, point, source):
        self._cached_pos[source] = point
        if source is not self._active_controller:
            return
        self._apply_pos(point)

    def set_size(self, size, scale, source):
        self._cached_size[source] = size
        self._cached_scale[source] = scale
        if source is not self._active_controller:
            return
        self._apply_size(size, scale)

    def update_controller_active(self, controller, active):
        last_active = self._active_controller
        if active:
            if controller not in self._active_controllers:
                self._active_controllers.append(controller)
        elif controller in self._active_controllers:
            self._active_controllers.remove(controller)
        new_active = self._active_controller
        if last_active == new_active:
            return

        self._apply_cached_values()
        self._update_visibility()
        self.activeChanged.emit(self.active)

    @property
    def _active_controller(self):
        return self._active_controllers[0] if self._active_controllers else None

    @Slot()
    def _update_visibility(self):
        if not self._target:
            return
        self._target.setVisible(self.active)

    def _apply_pos(self, pos):
        if not self._target:
            return
        # pos is global pos
        offset = self._target.mapToScene(QPointF()) - QPointF(
            self._target.x(), self._target.y()
        )
        local_pos = pos - offset
        self._target.setX(local_pos.x())
        self._target.setY(local_pos.y())

    def _apply_size(self, size, scale):
        if not self._target:
            return
        self._target.setWidth(size.width() * scale)
        self._target.setHeight(size.height() * scale)
        self._scale = scale
        self.scaleChanged.emit(scale)

    @Slot()
    def _apply_cached_values(self):
        if not (self._target and self._active_controller):
            return
        self._apply_pos(
            self._cached_pos.get(self._active_controller, QPointF())
        )
        self._apply_size(
            self._cached_size.get(self._active_controller, QRectF()),
            self._cached_scale.get(self._active_controller, 1.0),
        )

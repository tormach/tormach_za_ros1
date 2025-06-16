from PySide6.QtCore import Signal, Property, Slot
from PySide6.QtQml import QmlElement


from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class MoveBlockData(BlockData):
    """
    Provides a read-only interface to move block in QML.
    """

    waypointChanged = Signal()
    velocityChanged = Signal()
    accelerationChanged = Signal()
    velocityScaleChanged = Signal()
    accelerationScaleChanged = Signal()
    velocityIsScaleChanged = Signal()
    accelerationIsScaleChanged = Signal()
    durationChanged = Signal()
    probeModeChanged = Signal()
    strictLimitsChanged = Signal()

    DEFAULT_WAYPOINT = [0.0] * 6
    TYPES = 'movel', 'movej', 'movef'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.waypointChanged)
        self.dataChanged.connect(self._update_velocity)
        self.dataChanged.connect(self._update_acceleration)
        self.dataChanged.connect(self.durationChanged)
        self.dataChanged.connect(self.probeModeChanged)
        self.dataChanged.connect(self.strictLimitsChanged)

    @Property('QVariant', notify=waypointChanged)
    def waypoint(self):
        return self._get_block_data(
            'waypoint', self.DEFAULT_WAYPOINT, self.TYPES
        )

    @Property(float, notify=velocityChanged)
    def velocity(self):
        return self._velocity

    @Property(float, notify=velocityScaleChanged)
    def velocityScale(self):
        return self._velocity_scale

    @Property(bool, notify=velocityIsScaleChanged)
    def velocityIsScale(self):
        return self._velocity_is_scale

    @Property(float, notify=accelerationChanged)
    def acceleration(self):
        return self._acceleration

    @Property(float, notify=accelerationScaleChanged)
    def accelerationScale(self):
        return self._acceleration_scale

    @Property(bool, notify=accelerationIsScaleChanged)
    def accelerationIsScale(self):
        return self._acceleration_is_scale

    @Property(float, notify=durationChanged)
    def duration(self):
        return self._get_block_data('duration', 0.0, self.TYPES)

    @Property(int, notify=probeModeChanged)
    def probeMode(self):
        return self._get_block_data('probe_mode', 0, self.TYPES)

    @Property(bool, notify=strictLimitsChanged)
    def strictLimits(self):
        return self._get_block_data('strict_limits', False, self.TYPES)

    @Slot()
    def _update_velocity(self):
        velocity = self._get_block_data('velocity', None, self.TYPES)
        velocity_scale = self._get_block_data(
            'velocity_scale', None, self.TYPES
        )
        if velocity is not None:
            self._velocity = velocity
            self._velocity_scale = 1.0
            self._velocity_is_scale = False
        elif velocity_scale is not None:
            self._velocity = 0.0
            self._velocity_scale = velocity_scale
            self._velocity_is_scale = True
        else:
            self._velocity = 0.0
            self._velocity_scale = 1.0
            self._velocity_is_scale = False
        self.velocityChanged.emit()
        self.velocityScaleChanged.emit()
        self.velocityIsScaleChanged.emit()

    @Slot()
    def _update_acceleration(self):
        acceleration = self._get_block_data('acceleration', None, self.TYPES)
        acceleration_scale = self._get_block_data(
            'acceleration_scale', None, self.TYPES
        )
        if acceleration is not None:
            self._acceleration = acceleration
            self._acceleration_scale = 1.0
            self._acceleration_is_scale = False
        elif acceleration_scale is not None:
            self._acceleration = 0.0
            self._acceleration_scale = acceleration_scale
            self._acceleration_is_scale = True
        else:
            self._acceleration = 0.0
            self._acceleration_scale = 0.5
            self._acceleration_is_scale = False
        self.accelerationChanged.emit()
        self.accelerationScaleChanged.emit()
        self.accelerationIsScaleChanged.emit()

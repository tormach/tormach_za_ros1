from PySide6.QtCore import Property, Signal, QObject
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class Joint(QObject):
    POSITION_TOLERANCE = 0.0001
    VELOCITY_TOLERANCE = 0.001
    EFFORT_TOLERANCE = 0.001

    minimumChanged = Signal(float)
    maximumChanged = Signal(float)
    zeroChanged = Signal(float)
    positionChanged = Signal(float)
    velocityChanged = Signal(float)
    effortChanged = Signal(float)
    continuousChanged = Signal(bool)

    def __init__(
        self,
        parent=None,
        minimum=0.0,
        maximum=0.0,
        zero=0.0,
        position=0.0,
        velocity=0.0,
        effort=0.0,
        continuous=True,
    ):
        super().__init__(parent)

        self._minimum = minimum
        self._maximum = maximum
        self._zero = zero
        self._continuous = continuous

        self._position = position
        self._velocity = velocity
        self._effort = effort

    @Property(float, notify=minimumChanged)
    def minimum(self):
        return self._minimum

    @Property(float, notify=maximumChanged)
    def maximum(self):
        return self._maximum

    @Property(float, notify=zeroChanged)
    def zero(self):
        return self._zero

    @Property(bool, notify=continuousChanged)
    def continuous(self):
        return self._continuous

    @Property(float, notify=positionChanged)
    def position(self):
        return self._position

    @Property(float, notify=velocityChanged)
    def velocity(self):
        return self._velocity

    @Property(float, notify=effortChanged)
    def effort(self):
        return self._effort

    def update_from_joint_state(
        self,
        state,
        index,
        position_tolerance=POSITION_TOLERANCE,
        velocity_tolerance=VELOCITY_TOLERANCE,
        effort_tolerance=EFFORT_TOLERANCE,
    ):
        if len(state.name) < index:
            return
        if state.position and not self._isclose(
            self._position,
            state.position[index],
            abs_tol=position_tolerance,
        ):
            self._position = state.position[index]
            self.positionChanged.emit(self._position)
        if state.velocity and not self._isclose(
            self._velocity,
            state.velocity[index],
            abs_tol=velocity_tolerance,
        ):
            self._velocity = state.velocity[index]
            self.velocityChanged.emit(self._velocity)
        if state.effort and not self._isclose(
            self._effort, state.effort[index], abs_tol=effort_tolerance
        ):
            self._effort = state.effort[index]
            self.effortChanged.emit(self._effort)

    @staticmethod
    def _isclose(a, b, abs_tol):
        return abs(a - b) <= abs_tol

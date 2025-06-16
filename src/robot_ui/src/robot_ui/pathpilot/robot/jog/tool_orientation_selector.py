from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement
from PyKDL import Frame, Rotation
import numpy as np

from .. import Pose
from ..pose_conversions import ros_pose_to_kdl_frame

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ToolOrientationSelector(QObject):
    aChanged = Signal(float)
    bChanged = Signal(float)
    cChanged = Signal(float)
    inverseChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._a = 0
        self._b = 0
        self._c = 0
        self._inverse = False
        self._currentPose = Pose()

    @Slot(int, int, int)
    def setAxes(self, x_index, y_index, z_index):
        def index_to_vector(idx):
            if idx < 0:
                return None
            switch = {
                -1: None,
                0: np.array([1, 0, 0]),
                1: np.array([-1, 0, 0]),
                2: np.array([0, 1, 0]),
                3: np.array([0, -1, 0]),
                4: np.array([0, 0, 1]),
                5: np.array([0, 0, -1]),
            }
            return switch.get(idx)

        x = index_to_vector(x_index)
        y = index_to_vector(y_index)
        z = index_to_vector(z_index)
        if x is None:
            x = np.cross(y, z)
        if y is None:
            y = np.cross(z, x)
        if z is None:
            z = np.cross(x, y)
        r = Rotation(x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2])
        f = Frame()
        f.M = r

        if self._inverse:
            f_ga = Frame()
            f_ga.M = ros_pose_to_kdl_frame(self._currentPose.to_ros_pose()).M
            f = f_ga.Inverse() * f

        self._c, self._b, self._a = f.M.GetEulerZYX()
        self.aChanged.emit(self._a)
        self.bChanged.emit(self._b)
        self.cChanged.emit(self._c)

    @Property(float, notify=aChanged)
    def a(self):
        return self._a

    @Property(float, notify=bChanged)
    def b(self):
        return self._b

    @Property(float, notify=cChanged)
    def c(self):
        return self._c

    @Property(bool, notify=inverseChanged)
    def inverse(self):
        return self._inverse

    @inverse.setter
    def inverse(self, value):
        if value == self._inverse:
            return
        self._inverse = value
        self.inverseChanged.emit(value)

    @Property(Pose, constant=True)
    def currentPose(self):
        return self._currentPose

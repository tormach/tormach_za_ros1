from PySide6.QtQml import (
    QQmlPropertyMap,
    QQmlEngine,
    QmlElement,
    qmlContext,
)
from PySide6.QtCore import Property, Signal, QObject, Slot
from PySide6.QtGui import QVector3D, QQuaternion

from geometry_msgs.msg import Pose as RosPose
from geometry_msgs.msg import Vector3, Quaternion
from tf.transformations import euler_from_quaternion, quaternion_from_euler

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class Pose(QObject):
    # absolute tolerance before updating position values from ROS poses
    POSITION_TOLERANCE = 0.00005
    # absolute tolerance before updating orientation values from ROS poses
    ORIENTATION_TOLERANCE = 0.0005

    orientationChanged = Signal(QQuaternion)
    positionChanged = Signal(QVector3D)

    def __init__(self, parent=None, position=None, orientation=None):
        super().__init__(parent)

        self._orientation = orientation or QQuaternion()
        self._position = position or QVector3D()
        self._axis_positions = QQmlPropertyMap()
        self._axis_positions.valueChanged.connect(
            self._on_axis_positions_changed
        )
        # set when positions are updated manually
        self._axis_positions_updating = False

        self._update_axis_positions()

    @Slot(result='QVariant')
    @Slot(QObject, result='QVariant')
    def copy(self, parent=None):
        pose = Pose(position=self._position, orientation=self._orientation)
        # for QML it is required to give the new pose
        # a parent before changing the ownership
        if not parent:
            parent = qmlContext(self)
        if parent:
            pose.setParent(parent)
            QQmlEngine.setObjectOwnership(pose, QQmlEngine.JavaScriptOwnership)
        return pose

    @Property(QQuaternion, notify=orientationChanged)
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = value
        self.orientationChanged.emit(value)
        self._update_axis_positions()

    @Property(QVector3D, notify=positionChanged)
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.positionChanged.emit(value)
        self._update_axis_positions()

    @Property(QQmlPropertyMap, constant=True)
    def axisPositions(self):
        """
        :return: Object containing the axis positions in cartesian and Euler angle format.
        """
        return self._axis_positions

    @staticmethod
    def _isclose(a, b, abs_tol):
        return abs(a - b) <= abs_tol

    def update_from_ros_pose(
        self,
        pose,
        position_tolerance=POSITION_TOLERANCE,
        orientation_tolerance=ORIENTATION_TOLERANCE,
    ):
        changed = False
        p = pose.position
        if not (
            self._isclose(p.x, self._position.x(), abs_tol=position_tolerance)
            and self._isclose(
                p.y, self._position.y(), abs_tol=position_tolerance
            )
            and self._isclose(
                p.z, self._position.z(), abs_tol=position_tolerance
            )
        ):
            self._position.setX(p.x)
            self._position.setY(p.y)
            self._position.setZ(p.z)
            self.positionChanged.emit(self._position)
            changed = True

        o = pose.orientation
        if not (
            self._isclose(
                o.w, self._orientation.scalar(), abs_tol=orientation_tolerance
            )
            and self._isclose(
                o.x, self._orientation.x(), abs_tol=orientation_tolerance
            )
            and self._isclose(
                o.y, self._orientation.y(), abs_tol=orientation_tolerance
            )
            and self._isclose(
                o.z, self._orientation.z(), abs_tol=orientation_tolerance
            )
        ):
            self._orientation.setScalar(o.w)
            self._orientation.setX(o.x)
            self._orientation.setY(o.y)
            self._orientation.setZ(o.z)
            self.orientationChanged.emit(self._orientation)
            changed = True

        if changed:
            self._update_axis_positions()

    def to_ros_pose(self):
        pose = RosPose()
        pose.position = Vector3(
            x=self._position.x(), y=self._position.y(), z=self._position.z()
        )
        pose.orientation = Quaternion(
            x=self._orientation.x(),
            y=self._orientation.y(),
            z=self._orientation.z(),
            w=self._orientation.scalar(),
        )
        return pose

    @Slot(result=list)
    def toEulerAngles(self):
        euler = self._get_euler_angles(self._orientation)
        return [
            self._position.x(),
            self._position.y(),
            self._position.z(),
            euler[0],
            euler[1],
            euler[2],
        ]

    @Slot(result=str)
    def toEulerString(self, precision=2):
        euler = self._get_euler_angles(self._orientation)
        return "[{x},{y},{z},{a},{b},{c}]".format(
            x=round(self._position.x(), precision),
            y=round(self._position.y(), precision),
            z=round(self._position.z(), precision),
            a=round(euler[0], precision),
            b=round(euler[1], precision),
            c=round(euler[2], precision),
        )

    @staticmethod
    def from_euler_list(euler):
        pose = Pose()
        pose._axis_positions_updating = True
        pose._axis_positions.insert('x', euler[0])
        pose._axis_positions.insert('y', euler[1])
        pose._axis_positions.insert('z', euler[2])
        pose._axis_positions.insert('a', euler[3])
        pose._axis_positions.insert('b', euler[4])
        pose._axis_positions.insert('c', euler[5])
        pose._update_position(x=euler[0], y=euler[1], z=euler[2])
        pose._update_orientation(a=euler[3], b=euler[4], c=euler[5])
        pose._axis_positions_updating = False
        return pose

    @staticmethod
    def from_ros_pose(ros_pose):
        pose = Pose()
        pose.update_from_ros_pose(ros_pose)
        return pose

    def compare(self, other, position_tolerance, orientation_tolerance):
        """Compares two positions using position and orientation tolerance
        :param other: The other pose.
        :param position_tolerance: Match when position A is inside
        a sphere of this radius around B.
        :param orientation_tolerance: Match when all Euler angles of A
        are smaller or equal than all Euler angles of B.
        :return True when poses are similar, False when not
        """
        p1 = self._position
        p2 = other.position
        position_match = (
            abs(p1.x() - p2.x()) <= position_tolerance
            and abs(p1.y() - p2.y()) <= position_tolerance
            and abs(p1.z() - p2.z()) <= position_tolerance
        )
        o1 = self._orientation
        o2 = other.orientation
        orientation_match = (
            abs(o1.x() - o2.x()) <= orientation_tolerance
            and abs(o1.y() - o2.y()) <= orientation_tolerance
            and abs(o1.z() - o2.z()) <= orientation_tolerance
            and abs(o1.scalar() - o2.scalar()) <= orientation_tolerance
        )
        return position_match and orientation_match

    def _update_axis_positions(self):
        if self._axis_positions_updating:
            return
        self._axis_positions.insert('x', self._position.x())
        self._axis_positions.insert('y', self._position.y())
        self._axis_positions.insert('z', self._position.z())
        euler = self._get_euler_angles(self._orientation)
        self._axis_positions.insert('a', euler[0])
        self._axis_positions.insert('b', euler[1])
        self._axis_positions.insert('c', euler[2])

    @staticmethod
    def _get_euler_angles(orientation):
        quaternion = [
            orientation.x(),
            orientation.y(),
            orientation.z(),
            orientation.scalar(),
        ]
        return euler_from_quaternion(
            quaternion, axes='sxyz'
        )  # static/fixed frame XYZ

    @staticmethod
    def _get_orientation_from_euler(a, b, c):
        q = quaternion_from_euler(a, b, c, axes='sxyz')
        return QQuaternion(q[3], q[0], q[1], q[2])

    def _update_position(self, x=None, y=None, z=None):
        if x is not None:
            self._position.setX(x)
        if y is not None:
            self._position.setY(y)
        if z is not None:
            self._position.setZ(z)
        self.positionChanged.emit(self._position)

    def _update_orientation(self, a=None, b=None, c=None):
        a = self._axis_positions.value('a') if a is None else a
        b = self._axis_positions.value('b') if b is None else b
        c = self._axis_positions.value('c') if c is None else c
        self._orientation = self._get_orientation_from_euler(a, b, c)
        self.orientationChanged.emit(self._orientation)

    @Slot(str, 'QVariant')
    def _on_axis_positions_changed(self, key, value):
        switch = {
            'x': lambda: self._update_position(x=value),
            'y': lambda: self._update_position(y=value),
            'z': lambda: self._update_position(z=value),
            'a': lambda: self._update_orientation(a=value),
            'b': lambda: self._update_orientation(b=value),
            'c': lambda: self._update_orientation(c=value),
        }
        self._axis_positions_updating = True
        switch.get(key, lambda: None)()
        self._axis_positions_updating = False

    def __str__(self):
        return 'Pose( position={}, orientation={} )'.format(
            self._position, self._orientation
        )

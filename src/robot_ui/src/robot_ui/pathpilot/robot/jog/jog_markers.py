from math import pi
from PySide6.QtQml import QQmlPropertyMap, QPyQmlParserStatus, QmlElement
from PySide6.QtCore import Property, Signal, Slot, QTimer, QObject

import rospy
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Pose as RosPose
from robot_common.joint_urdf import read_robot_description

from ...base.resource_paths import STL_PATH
from ...qt_helpers import ensure_cleanup
from .. import Pose
from ..pose_conversions import pose_list_to_ros_pose

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class JogMarkers(QPyQmlParserStatus):
    MARKER_TOPIC = '/pose_marker_array'
    MARKER_NS = 'jog_markers'
    RESOURCE_BASE_PATH = f'file://{STL_PATH}'
    AXIS_NAMES = ('x', 'y', 'z', 'a', 'b', 'c')
    LINEAR_AXIS_NAMES = ('x', 'y', 'z')
    MARKER_COLORS = {
        'x': (1.0, 0.0, 0.0),
        'y': (0.0, 1.0, 0.0),
        'z': (0.0, 0.0, 1.0),
        'a': (1.0, 0.0, 0.0),
        'b': (0.0, 1.0, 0.0),
        'c': (0.0, 0.0, 1.0),
        'joint': (1.0, 1.0, 0.0),
    }
    DEFAULT_UPDATE_INTERVAL = 500

    xMinusActiveChanged = Signal(bool)
    xPlusActiveChanged = Signal(bool)
    yMinusActiveChanged = Signal(bool)
    yPlusActiveChanged = Signal(bool)
    zMinusActiveChanged = Signal(bool)
    zPlusActiveChanged = Signal(bool)
    aMinusActiveChanged = Signal(bool)
    aPlusActiveChanged = Signal(bool)
    bMinusActiveChanged = Signal(bool)
    bPlusActiveChanged = Signal(bool)
    cMinusActiveChanged = Signal(bool)
    cPlusActiveChanged = Signal(bool)
    markerFrameChanged = Signal(str)
    markerPoseChanged = Signal()
    useToolFrameChanged = Signal(bool)
    updateIntervalChanged = Signal(int)
    baseLinkChanged = Signal(str)
    jointNamePrefixChanged = Signal(str)

    def __init__(
        self,
        parent=None,
        marker_frame='world',
        update_interval=DEFAULT_UPDATE_INTERVAL,
        base_link='',
        joint_name_prefix='',
    ):
        super().__init__(parent)
        self._x_minus_active = False
        self._x_plus_active = False
        self._y_minus_active = False
        self._y_plus_active = False
        self._z_minus_active = False
        self._z_plus_active = False
        self._a_minus_active = False
        self._a_plus_active = False
        self._b_minus_active = False
        self._b_plus_active = False
        self._c_minus_active = False
        self._c_plus_active = False
        self._use_tool_frame = False
        self._marker_frame = marker_frame
        self._marker_pose = Pose()
        self._update_interval = update_interval

        self._base_link = base_link
        self._joint_name_prefix = joint_name_prefix
        self._joint_order = []
        self._joint_map = {}
        self._joints = QQmlPropertyMap()

        self._publish_timer = QTimer(self)
        self._marker_pub = None

        ensure_cleanup(self._shutdown)

    def classBegin(self):
        pass

    def componentComplete(self):
        self._marker_pub = rospy.Publisher(
            self.MARKER_TOPIC, MarkerArray, queue_size=1
        )

        self._publish_timer.timeout.connect(self._publish_markers)
        self._joints.valueChanged.connect(self._on_value_changed)

        self.xMinusActiveChanged.connect(self._update)
        self.xPlusActiveChanged.connect(self._update)
        self.yMinusActiveChanged.connect(self._update)
        self.yPlusActiveChanged.connect(self._update)
        self.zMinusActiveChanged.connect(self._update)
        self.zPlusActiveChanged.connect(self._update)
        self.aMinusActiveChanged.connect(self._update)
        self.aPlusActiveChanged.connect(self._update)
        self.bMinusActiveChanged.connect(self._update)
        self.bPlusActiveChanged.connect(self._update)
        self.cMinusActiveChanged.connect(self._update)
        self.cPlusActiveChanged.connect(self._update)
        self.markerFrameChanged.connect(self._update)
        self.markerPoseChanged.connect(self._update)
        self.useToolFrameChanged.connect(self._update)
        self.updateIntervalChanged.connect(self._update)

        self._read_robot_description()

        self._publish_timer.start(self._update_interval)

    @Property(bool, notify=xMinusActiveChanged)
    def xMinusActive(self):
        return self._x_minus_active

    @xMinusActive.setter
    def xMinusActive(self, value):
        if value == self._x_minus_active:
            return
        self._x_minus_active = value
        self.xMinusActiveChanged.emit(value)

    @Property(bool, notify=xPlusActiveChanged)
    def xPlusActive(self):
        return self._x_plus_active

    @xPlusActive.setter
    def xPlusActive(self, value):
        if value == self._x_plus_active:
            return
        self._x_plus_active = value
        self.xPlusActiveChanged.emit(value)

    @Property(bool, notify=yMinusActiveChanged)
    def yMinusActive(self):
        return self._y_minus_active

    @yMinusActive.setter
    def yMinusActive(self, value):
        if value == self._y_minus_active:
            return
        self._y_minus_active = value
        self.yMinusActiveChanged.emit(value)

    @Property(bool, notify=yPlusActiveChanged)
    def yPlusActive(self):
        return self._y_plus_active

    @yPlusActive.setter
    def yPlusActive(self, value):
        if value == self._y_plus_active:
            return
        self._y_plus_active = value
        self.yPlusActiveChanged.emit(value)

    @Property(bool, notify=zMinusActiveChanged)
    def zMinusActive(self):
        return self._z_minus_active

    @zMinusActive.setter
    def zMinusActive(self, value):
        if value == self._z_minus_active:
            return
        self._z_minus_active = value
        self.zMinusActiveChanged.emit(value)

    @Property(bool, notify=zPlusActiveChanged)
    def zPlusActive(self):
        return self._z_plus_active

    @zPlusActive.setter
    def zPlusActive(self, value):
        if value == self._z_plus_active:
            return
        self._z_plus_active = value
        self.zPlusActiveChanged.emit(value)

    @Property(bool, notify=aMinusActiveChanged)
    def aMinusActive(self):
        return self._a_minus_active

    @aMinusActive.setter
    def aMinusActive(self, value):
        if value == self._a_minus_active:
            return
        self._a_minus_active = value
        self.aMinusActiveChanged.emit(value)

    @Property(bool, notify=aPlusActiveChanged)
    def aPlusActive(self):
        return self._a_plus_active

    @aPlusActive.setter
    def aPlusActive(self, value):
        if value == self._a_plus_active:
            return
        self._a_plus_active = value
        self.aPlusActiveChanged.emit(value)

    @Property(bool, notify=bMinusActiveChanged)
    def bMinusActive(self):
        return self._b_minus_active

    @bMinusActive.setter
    def bMinusActive(self, value):
        if value == self._b_minus_active:
            return
        self._b_minus_active = value
        self.bMinusActiveChanged.emit(value)

    @Property(bool, notify=bPlusActiveChanged)
    def bPlusActive(self):
        return self._b_plus_active

    @bPlusActive.setter
    def bPlusActive(self, value):
        if value == self._b_plus_active:
            return
        self._b_plus_active = value
        self.bPlusActiveChanged.emit(value)

    @Property(bool, notify=cMinusActiveChanged)
    def cMinusActive(self):
        return self._c_minus_active

    @cMinusActive.setter
    def cMinusActive(self, value):
        if value == self._c_minus_active:
            return
        self._c_minus_active = value
        self.cMinusActiveChanged.emit(value)

    @Property(bool, notify=cPlusActiveChanged)
    def cPlusActive(self):
        return self._c_plus_active

    @cPlusActive.setter
    def cPlusActive(self, value):
        if value == self._c_plus_active:
            return
        self._c_plus_active = value
        self.cPlusActiveChanged.emit(value)

    @Property(QQmlPropertyMap, constant=True)
    def activeJoints(self):
        return self._joints

    @Property(str, notify=markerFrameChanged)
    def markerFrame(self):
        return self._marker_frame

    @markerFrame.setter
    def markerFrame(self, value):
        if value == self._marker_frame:
            return
        self._marker_frame = value
        self.markerFrameChanged.emit(value)

    @Property(QObject, notify=markerPoseChanged)  # Pose
    def markerPose(self):
        return self._marker_pose

    @markerPose.setter
    def markerPose(self, value):
        if value == self._marker_pose:
            return
        self._marker_pose = value
        self.markerPoseChanged.emit()

    @Property(bool, notify=useToolFrameChanged)
    def useToolFrame(self):
        return self._use_tool_frame

    @useToolFrame.setter
    def useToolFrame(self, value):
        if value == self._use_tool_frame:
            return
        self._use_tool_frame = value
        self.useToolFrameChanged.emit(value)

    @Property(int, notify=updateIntervalChanged)
    def updateInterval(self):
        return self._update_interval

    @updateInterval.setter
    def updateInterval(self, value):
        if value == self._update_interval:
            return
        self._update_interval = value
        self.updateIntervalChanged.emit(value)

    @Property(str, notify=baseLinkChanged)
    def baseLink(self):
        return self._base_link

    @baseLink.setter
    def baseLink(self, value):
        if value == self._base_link:
            return
        self._base_link = value
        self.baseLinkChanged.emit(value)

    @Property(str, notify=jointNamePrefixChanged)
    def jointNamePrefix(self):
        return self._joint_name_prefix

    @jointNamePrefix.setter
    def jointNamePrefix(self, value):
        if value == self._joint_name_prefix:
            return
        self._joint_name_prefix = value
        self.jointNamePrefixChanged.emit(value)

    @Slot()
    def _update(self):
        self._publish_timer.stop()
        self._publish_markers()
        self._publish_timer.start(self._update_interval)

    @Slot()
    def _shutdown(self):
        self._publish_timer.stop()

    def _read_robot_description(self):
        joint_order = []
        for key in self._joints.keys():
            self._joints.clear(key)
        for i, node in enumerate(read_robot_description(self._base_link)):
            if self._joint_name_prefix and not node.name.startswith(
                self._joint_name_prefix
            ):
                continue

            joint_order.append(node)
            id_ = str(i + 1)
            self._joint_map[node.name] = id_
            self._joint_map[id_] = node.name
            self._joints.insert(node.name, 0)
            self._joints.insert(id_, 0)
        self._joint_order = joint_order

    @Slot()
    def _publish_markers(self):
        markers = MarkerArray()

        def create_axis_marker(axis_, direction_, id_):
            marker = Marker()
            marker.header.frame_id = self._marker_frame
            marker.header.stamp = rospy.Time.now()
            marker.ns = self.MARKER_NS
            marker.id = id_
            marker.type = Marker.MESH_RESOURCE
            marker.mesh_resource = (
                f'{self.RESOURCE_BASE_PATH}/{axis_}_{direction_}.stl'
            )
            marker.action = Marker.ADD
            pose = self._marker_pose.toEulerAngles()
            if not self._use_tool_frame:
                if axis_ == 'a':
                    pose[3] = pi / 2.0
                    pose[4] = 0.0
                    pose[5] = 0.0
                if axis_ == 'b':
                    pose[3] = 0.0
                    pose[4] = pi / 2.0
                    pose[5] = 0.0
                elif axis_ == 'c':
                    pose[3] = 0.0
                    pose[4] = 0.0
                    pose[5] = 0.0
                elif axis_ in self.LINEAR_AXIS_NAMES:
                    pose[3] = 0.0
                    pose[4] = 0.0
                    pose[5] = 0.0
            marker.pose = pose_list_to_ros_pose(pose)
            marker.scale.x = 1.0
            marker.scale.y = 1.0
            marker.scale.z = 1.0
            color = self.MARKER_COLORS[axis_]
            marker.color.a = 1.0
            marker.color.r = color[0]
            marker.color.g = color[1]
            marker.color.b = color[2]
            return marker

        def create_joint_marker(joint_, direction_, id_):
            marker = Marker()
            marker.header.frame_id = joint_.child
            marker.header.stamp = rospy.Time.now()
            marker.ns = self.MARKER_NS
            marker.id = id_
            marker.type = Marker.MESH_RESOURCE
            axes = tuple(int(float(j)) for j in joint_.axis.split(' '))
            if axes in [(1, 0, 0), (-1, 0, 0)]:
                axis_ = 'x'
            elif axes in [(0, 1, 0), (0, -1, 0)]:
                axis_ = 'y'
            elif axes in [(0, 0, 1), (0, 0, -1)]:
                axis_ = 'z'
            else:
                axis_ = 'x'
                rospy.logwarn(
                    "Unsupported joint configuration for marker display"
                )
            inverted = sum(axes) < 0

            marker.mesh_resource = (
                f'{self.RESOURCE_BASE_PATH}/joint_{axis_}_{direction_}.stl'
            )
            marker.action = Marker.ADD
            marker.pose = RosPose()
            marker.scale.x = 1.0
            marker.scale.y = -1.0 if inverted else 1.0
            marker.scale.z = 1.0
            color = self.MARKER_COLORS['joint']
            marker.color.a = 1.0
            marker.color.r = color[0]
            marker.color.g = color[1]
            marker.color.b = color[2]
            return marker

        def clear_marker(id_):
            marker = Marker()
            marker.ns = self.MARKER_NS
            marker.id = id_
            marker.action = Marker.DELETE
            return marker

        i = 0
        max_markers = (len(self.AXIS_NAMES) + len(self._joint_order)) * 2
        marker_ids = set(range(max_markers))
        for axis in self.AXIS_NAMES:
            for direction in ('plus', 'minus'):
                active = getattr(self, f'_{axis}_{direction}_active')
                if active:
                    markers.markers.append(
                        create_axis_marker(axis, direction, i)
                    )
                    marker_ids.remove(i)
                i += 1
        for joint in self._joint_order:
            for direction in ('plus', 'minus'):
                if direction == 'plus':
                    active = self._joints.value(joint.name) > 0
                else:
                    active = self._joints.value(joint.name) < 0
                if active:
                    markers.markers.append(
                        create_joint_marker(joint, direction, i)
                    )
                    marker_ids.remove(i)
                i += 1

        for i in marker_ids:
            markers.markers.append(clear_marker(i))

        self._marker_pub.publish(markers)

    @Slot(str, 'QVariant')
    def _on_value_changed(self, key, value):
        if key not in self._joint_map:
            return

        other = self._joint_map[key]
        self._joints.insert(other, value)
        self._update()

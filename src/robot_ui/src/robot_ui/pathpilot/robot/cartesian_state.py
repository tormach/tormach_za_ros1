from PySide6.QtCore import Property, Signal, QObject, Slot
from PySide6.QtQml import QmlElement

import rospy
from geometry_msgs.msg import PoseStamped
from robot_common.tools import get_param

from ..qt_helpers import ensure_cleanup
from .pose import Pose

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CartesianState(QObject):
    POSE_STATES_SOURCE_LIST_PARAM = "pose_states_source_list"
    WORLD_POSE_STATES_SOURCE_LIST_PARAM = "world_pose_states_source_list"

    positionToleranceChanged = Signal(float)
    orientationToleranceChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._pose = Pose()
        self._world_pose = Pose()
        self._position_tolerance = Pose.POSITION_TOLERANCE
        self._orientation_tolerance = Pose.ORIENTATION_TOLERANCE

        self._subs = []

        def subscribe(sources, function):
            for source in sources:
                sub = rospy.Subscriber(source, PoseStamped, function)
                self._subs.append(sub)

        source_list = get_param(self.POSE_STATES_SOURCE_LIST_PARAM, [])
        subscribe(source_list, self._pose_state_update_received)
        source_list = get_param(self.WORLD_POSE_STATES_SOURCE_LIST_PARAM, [])
        subscribe(source_list, self._world_pose_state_update_received)

        ensure_cleanup(self._shutdown)

    @Property(Pose, constant=True)
    def pose(self):
        return self._pose

    @Property(Pose, constant=True)
    def worldPose(self):
        return self._world_pose

    @Property(float, notify=positionToleranceChanged)
    def positionTolerance(self):
        return self._position_tolerance

    @positionTolerance.setter
    def positionTolerance(self, value):
        if value == self._position_tolerance:
            return
        self._position_tolerance = value
        self.positionToleranceChanged.emit(value)

    @Property(float, notify=orientationToleranceChanged)
    def orientationTolerance(self):
        return self._orientation_tolerance

    @orientationTolerance.setter
    def orientationTolerance(self, value):
        if value == self._orientation_tolerance:
            return
        self._orientation_tolerance = value
        self.orientationToleranceChanged.emit(value)

    def _pose_state_update_received(self, msg):
        self._pose.update_from_ros_pose(
            msg.pose,
            position_tolerance=self._position_tolerance,
            orientation_tolerance=self._orientation_tolerance,
        )

    def _world_pose_state_update_received(self, msg):
        self._world_pose.update_from_ros_pose(
            msg.pose,
            position_tolerance=self._position_tolerance,
            orientation_tolerance=self._orientation_tolerance,
        )

    @Slot()
    def _shutdown(self):
        for sub in self._subs:
            sub.unregister()

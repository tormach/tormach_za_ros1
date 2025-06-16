from PySide6.QtQml import QPyQmlParserStatus, QmlElement
from PySide6.QtCore import Property, Signal, Slot, QObject

import rospy
from visualization_msgs.msg import Marker, MarkerArray
from robot_command.rpl import Pose as TRPLPose
from robot_command.rpl import Joints as TRPLJoint
from ...qt_helpers import ensure_cleanup

from robot_command.waypoint import TargetType
from tf2_kdl import transform_to_kdl
from tf_conversions import posemath

from robot_command.interfaces import (
    JointsToPoseInterfaceSingleton,
    ConfigInterfaceSingleton,
    UserFrameInterfaceSingleton,
)


QML_IMPORT_NAME = 'pathpilot.robot.preview_waypoints'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WaypointMarkers(QPyQmlParserStatus):
    MARKER_TOPIC = '/waypoint_marker_array'
    MARKER_NS = 'waypoint_markers'

    globalWaypointsChanged = Signal(bool)
    programWaypointsChanged = Signal(bool)
    showGlobalWaypointsChanged = Signal(bool)
    showProgramWaypointsChanged = Signal(bool)
    activeWaypointNameChanged = Signal(str)

    def __init__(
        self,
        parent=None,
        marker_frame='world',
    ):
        super().__init__(parent)

        self._config = ConfigInterfaceSingleton()
        self._user_frames = UserFrameInterfaceSingleton()
        self._joints_to_pose = JointsToPoseInterfaceSingleton()

        self._global_waypoints = QObject()
        self._program_waypoints = QObject()
        self._active_waypoint_name = ""

        self._marker_pub = None
        self._show_global_waypoints = True
        self._show_program_waypoints = True

        ensure_cleanup(self._shutdown)

    def classBegin(self):
        pass

    def componentComplete(self):
        self._marker_pub = rospy.Publisher(
            self.MARKER_TOPIC, MarkerArray, queue_size=1, latch=True
        )

        self.showGlobalWaypointsChanged.connect(self._update)
        self.showProgramWaypointsChanged.connect(self._update)
        self.activeWaypointNameChanged.connect(self._update)

        self._update()

    @Property(QObject)
    def globalWaypoints(self):
        return self._global_waypoints

    @globalWaypoints.setter
    def globalWaypoints(self, value):
        if value == self._global_waypoints:
            return
        if self._global_waypoints:
            self._global_waypoints.disconnect(self)  # disconnect all signals
        self._global_waypoints = value
        if self._global_waypoints:
            self._global_waypoints.waypointsUpdated.connect(self._update)
            self._global_waypoints.reset.connect(self._update)

    @Property(bool, notify=showGlobalWaypointsChanged)
    def showGlobalWaypoints(self):
        return self._show_global_waypoints

    @showGlobalWaypoints.setter
    def showGlobalWaypoints(self, value):
        if value == self._show_global_waypoints:
            return
        self._show_global_waypoints = value
        self.showGlobalWaypointsChanged.emit(value)

    @Property(QObject)
    def programWaypoints(self):
        return self._program_waypoints

    @programWaypoints.setter
    def programWaypoints(self, value):
        if value == self._program_waypoints:
            return
        if self._program_waypoints:
            self._program_waypoints.disconnect(self)  # disconnect all signals
        self._program_waypoints = value
        if self._program_waypoints:
            self._program_waypoints.waypointsUpdated.connect(self._update)
            self._program_waypoints.reset.connect(self._update)

    @Property(bool, notify=showProgramWaypointsChanged)
    def showProgramWaypoints(self):
        return self._show_program_waypoints

    @showProgramWaypoints.setter
    def showProgramWaypoints(self, value):
        if value == self._show_program_waypoints:
            return
        self._show_program_waypoints = value
        self.showProgramWaypointsChanged.emit(value)

    @Property(str, notify=activeWaypointNameChanged)
    def activeWaypointName(self):
        return self._active_waypoint_name

    @activeWaypointName.setter
    def activeWaypointName(self, value):
        if value == self._active_waypoint_name:
            return
        self._active_waypoint_name = value
        self.activeWaypointNameChanged.emit(value)

    @Slot()
    def _update(self):
        self._publish_markers()

    @Slot()
    def _shutdown(self):
        pass

    @Slot()
    def _publish_markers(self):
        markers = MarkerArray()

        def clear_markers():
            marker = Marker()
            marker.header.frame_id = "world"
            marker.header.stamp = rospy.Time.now()
            marker.ns = self.MARKER_NS
            marker.id = 0
            marker.action = Marker.DELETEALL
            return marker

        def create_markers(poses, names):
            markers = MarkerArray()
            markers.markers.append(clear_markers())
            for i, pose in enumerate(poses):
                pose = pose.to_ros_units()
                marker = Marker()
                marker.header.frame_id = "world"
                marker.header.stamp = rospy.Time.now()
                marker.ns = "global_markers"
                marker.id = i * 2
                marker.type = Marker.CUBE
                marker.action = Marker.ADD

                marker.pose = pose.to_ros_pose()
                # Determine the scale based on the active waypoint. If it is not active, make it slightly smaller to handle edge case of an active and inactive waypoint ontop of each other.
                scale_value = (
                    0.02
                    if not self._active_waypoint_name
                    or self._active_waypoint_name == names[i]
                    else 0.019
                )

                # Assign the scale values
                marker.scale.x = scale_value
                marker.scale.y = scale_value
                marker.scale.z = scale_value

                # Determine alpha value for the color. Deemphasize the inactive waypoints.
                alpha_value = (
                    1.0
                    if not self._active_waypoint_name
                    or self._active_waypoint_name == names[i]
                    else 0.5
                )
                marker.color.a = alpha_value

                # Determine RGB values based on the active waypoint
                red_value = (
                    0 / 255
                    if self._active_waypoint_name != names[i]
                    else 250 / 255
                )
                green_value = (
                    210 / 255
                    if self._active_waypoint_name != names[i]
                    else 128 / 255
                )
                blue_value = (
                    211 / 255
                    if self._active_waypoint_name != names[i]
                    else 0 / 255
                )

                # Assign the RGB values
                marker.color.r = red_value
                marker.color.g = green_value
                marker.color.b = blue_value

                markers.markers.append(marker)

                marker = Marker()
                marker.header.frame_id = "world"
                marker.header.stamp = rospy.Time.now()
                marker.ns = "global_markers"
                marker.id = i * 2 + 1
                marker.type = Marker.TEXT_VIEW_FACING
                marker.action = Marker.ADD
                pose = pose.copy()
                pose.z += 0.04
                marker.pose = pose.to_ros_pose()
                marker.scale.x = 0.03
                marker.scale.y = 0.03
                marker.scale.z = 0.03
                marker.color.a = (
                    1.0
                    if not self._active_waypoint_name
                    or self._active_waypoint_name == names[i]
                    else 0.75
                )
                marker.color.r = 1.0
                marker.color.g = 1.0
                marker.color.b = 1.0
                marker.text = names[i]
                markers.markers.append(marker)
            return markers

        def process_waypoints(
            waypoints, marker_obj_list, marker_name_list, program=False
        ):
            if waypoints is not None:
                for wp in waypoints:
                    if wp.target_type == TargetType.Pose:
                        wp_pose = TRPLPose.from_list(wp.target)
                        if program:
                            wp_pose = wp_pose.to_ros_units(
                                self._config.linear_unit,
                                self._config.angular_unit,
                            )

                        # Offset for user frames
                        if active_frame := self._user_frames.active_frame:
                            if transform := self._user_frames.get_transform(
                                active_frame
                            ):
                                wp_pose = posemath.toMsg(
                                    transform_to_kdl(transform)
                                    * posemath.fromMsg(
                                        TRPLPose.to_ros_pose(wp_pose)
                                    )
                                )
                                wp_pose = TRPLPose.from_ros_pose(wp_pose)

                    else:  # Joint waypoint
                        target = TRPLJoint.from_list(wp.target)
                        if program:
                            target = target.to_ros_units(
                                self._config.angular_unit
                            )

                        from_joint_to_ros_pos = (
                            self._joints_to_pose.get_pose_from_joint_values(
                                target.to_list()
                            )
                        )
                        wp_pose = TRPLPose.from_ros_pose(from_joint_to_ros_pos)

                    marker_obj_list.append(wp_pose)
                    marker_name_list.append(str(wp.name))

        marker_objs = []
        marker_names = []

        if self._show_program_waypoints and self._program_waypoints is not None:
            process_waypoints(
                self._program_waypoints.waypoints,
                marker_objs,
                marker_names,
                program=True,
            )

        if self._show_global_waypoints and self._global_waypoints is not None:
            process_waypoints(
                self._global_waypoints.waypoints, marker_objs, marker_names
            )

        if len(marker_objs) == 0:
            markers.markers.append(clear_markers())
            self._marker_pub.publish(markers)
            return

        marker_list = create_markers(
            marker_objs,
            marker_names,
        )

        for waypoint_marker in marker_list.markers:
            markers.markers.append(waypoint_marker)

        self._marker_pub.publish(markers)

import contextlib

from PySide6.QtCore import Property, Slot, Signal, QObject, QTimer
from PySide6.QtQml import QmlElement
from uuid import uuid4

import rospy
from visualization_msgs.msg import (
    InteractiveMarkerFeedback,
    InteractiveMarkerUpdate,
    InteractiveMarkerPose,
)
from std_msgs.msg import Header
from geometry_msgs.msg import Pose as RosPose

from ...robot import Pose
from ...robot.pose_conversions import (
    pose_list_to_kdl_frame,
    ros_pose_to_kdl_frame,
    kdl_frame_to_ros_pose,
)
from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class InteractiveMarker(QObject):
    """
    The InteractiveMarker component provides an interface to existing interactive markers.

    """

    FEEDBACK_TOPIC = '/rviz_moveit_motion_planning_display/robot_interaction_interactive_marker_topic/feedback'
    UPDATE_TOPIC = '/rviz_moveit_motion_planning_display/robot_interaction_interactive_marker_topic/update'
    KEEP_ALIVE_INTERVAL_MS = 500
    PUBLISH_UPDATE_DELAY_MS = 50

    validChanged = Signal(bool)
    fixedFrameChanged = Signal(str)
    markerNameChanged = Signal(str)
    framesChanged = Signal()

    def __init__(
        self,
        parent=None,
        fixed_frame='/world',
        marker_name='EE:goal_tool0',
        frames=None,
    ):
        super().__init__(parent)

        self._pose = Pose()
        self._valid = False
        self._seq_num = 0
        self._server_id = f'/robot_ui_marker_{uuid4()}'
        self._fixed_frame = fixed_frame
        self._marker_name = marker_name
        self._frames = frames
        self._world_pose = RosPose()

        self._fb_sub = rospy.Subscriber(
            self.FEEDBACK_TOPIC,
            InteractiveMarkerFeedback,
            self._feedback_received,
        )
        self._update_pub = rospy.Publisher(
            self.UPDATE_TOPIC,
            InteractiveMarkerUpdate,
            queue_size=1,
        )
        self._fb_pub = rospy.Publisher(
            self.FEEDBACK_TOPIC,
            InteractiveMarkerFeedback,
            queue_size=1,
        )

        self._keep_alive_timer = QTimer(self)
        self._keep_alive_timer.timeout.connect(self._publish_keep_alive)
        self._keep_alive_timer.setInterval(self.KEEP_ALIVE_INTERVAL_MS)
        self._keep_alive_timer.start()

        self._publish_update_timer = QTimer(self)
        self._publish_update_timer.timeout.connect(
            self._publish_update_timer_tick
        )
        self._publish_update_timer.setInterval(self.PUBLISH_UPDATE_DELAY_MS)

        ensure_cleanup(self._shutdown)

    @Property(Pose, constant=True)
    def pose(self):
        return self._pose

    @Property(bool, notify=validChanged)
    def valid(self):
        return self._valid

    @Property(str, notify=fixedFrameChanged)
    def fixedFrame(self):
        return self._fixed_frame

    @fixedFrame.setter
    def fixedFrame(self, value):
        if value == self._fixed_frame:
            return
        self._fixed_frame = value
        self.fixedFrameChanged.emit(value)

    @Property(str, notify=markerNameChanged)
    def markerName(self):
        return self._marker_name

    @markerName.setter
    def markerName(self, value):
        if value == self._marker_name:
            return
        self._marker_name = value
        self.markerNameChanged.emit(value)

    @Property(QObject, notify=framesChanged)  # Frames type
    def frames(self):
        return self._frames

    @frames.setter
    def frames(self, value):
        if value == self._frames:
            return
        if self._frames:
            with contextlib.suppress(RuntimeError):
                self._frames.activeFramePoseChanged.disconnect(
                    self._update_pose_from_world_pose
                )
        self._frames = value
        if self._frames:
            self._frames.activeFramePoseChanged.connect(
                self._update_pose_from_world_pose
            )
        self.framesChanged.emit()

    @Slot()
    def publish(self):
        self._publish_pre_update()
        self._publish_update_timer.stop()
        self._publish_update_timer.start()

    @Slot()
    def _shutdown(self):
        self._keep_alive_timer.stop()
        self._publish_update_timer.stop()
        self._fb_sub.unregister()
        # self._update_pub.unregister()
        # self._fb_pub.unregister()

    def _transform_world_pose_to_frame(self, world_pose):
        if not self._frames:
            return world_pose
        frame_f = pose_list_to_kdl_frame(self._frames.activeFramePose)
        world_pose_f = ros_pose_to_kdl_frame(world_pose)
        pose_f = frame_f.Inverse() * world_pose_f
        return kdl_frame_to_ros_pose(pose_f)

    def _transform_frame_pose_to_world_pose(self, pose):
        if not self._frames:
            return pose
        frame_f = pose_list_to_kdl_frame(self._frames.activeFramePose)
        pose_f = ros_pose_to_kdl_frame(pose)
        world_pose_f = frame_f * pose_f
        return kdl_frame_to_ros_pose(world_pose_f)

    @Slot()
    def _update_pose_from_world_pose(self):
        pose = self._transform_world_pose_to_frame(self._world_pose)
        self._pose.update_from_ros_pose(
            pose,
            position_tolerance=0.0,
        )

    def _feedback_received(self, msg):
        if msg.client_id == self._server_id:
            return
        if msg.marker_name != self._marker_name:
            return

        self._world_pose = msg.pose
        self._update_pose_from_world_pose()
        self._valid = True
        self.validChanged.emit(self._valid)

    def _publish_pre_update(self):
        world_pose = self._transform_frame_pose_to_world_pose(
            self._pose.to_ros_pose()
        )
        world_pose.position.x += 0.01  # slight offset to nudge the marker
        fb_msg = InteractiveMarkerFeedback(
            header=Header(
                frame_id=self._fixed_frame,
                seq=self._seq_num,
                stamp=rospy.Time.now(),
            ),
            client_id=self._server_id,
            marker_name=self._marker_name,
            control_name='_robot_ui',  # original _u1, doesn't matter
            event_type=InteractiveMarkerFeedback.POSE_UPDATE,
            pose=world_pose,
        )
        self._fb_pub.publish(fb_msg)

    def _publish_update(self):
        self._world_pose = self._transform_frame_pose_to_world_pose(
            self._pose.to_ros_pose()
        )
        stamp = rospy.Time.now()
        update_msg = InteractiveMarkerUpdate(
            server_id=self._server_id,
            seq_num=self._seq_num,
            type=InteractiveMarkerUpdate.UPDATE,
        )
        fb_msg = InteractiveMarkerFeedback(
            header=Header(
                frame_id=self._fixed_frame, seq=self._seq_num, stamp=stamp
            ),
            client_id=self._server_id,
            marker_name=self._marker_name,
            control_name='_robot_ui',  # original _u1, doesn't matter
            event_type=InteractiveMarkerFeedback.POSE_UPDATE,
            pose=self._world_pose,
        )
        marker_pose = InteractiveMarkerPose(
            header=Header(frame_id=self._fixed_frame, stamp=stamp),
            pose=self._world_pose,
            name=self._marker_name,
        )
        update_msg.poses.append(marker_pose)
        self._update_pub.publish(update_msg)
        self._fb_pub.publish(fb_msg)

        self._seq_num += 1

        if not self._valid:
            self._valid = True
            self.validChanged.emit(self._valid)

    @Slot()
    def _publish_keep_alive(self):
        msg = InteractiveMarkerUpdate(
            server_id=self._server_id,
            seq_num=self._seq_num,
            type=InteractiveMarkerUpdate.KEEP_ALIVE,
        )
        self._update_pub.publish(msg)

    @Slot()
    def _publish_update_timer_tick(self):
        self._publish_update_timer.stop()
        self._publish_update()

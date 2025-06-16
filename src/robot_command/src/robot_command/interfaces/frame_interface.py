import time
from collections import namedtuple

import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped
from tf2_geometry_msgs import tf2_geometry_msgs

from robot_command.rpl import Pose
from robot_frame import FrameClient

FrameItem = namedtuple('FrameItem', 'pose transform')


class FrameInterface:
    DEFAULT_WAIT_TIMEOUT_S = 10.0
    TF_BUFFER_CACHE_TIME_S = 1200
    TF_WAIT_TIMEOUT_S = 1.0
    TF_SYNC_TIME_S = 0.01

    def __init__(self, namespace, pose_reference_frame, tf_buffer=None):
        self._namespace = namespace
        self.pose_reference_frame = pose_reference_frame

        if not tf_buffer:
            self._tf_buffer = tf2_ros.Buffer(
                cache_time=rospy.Duration.from_sec(self.TF_BUFFER_CACHE_TIME_S)
            )
            self._tf_listener = tf2_ros.TransformListener(self._tf_buffer)
        else:
            self._tf_buffer = tf_buffer
            self._tf_listener = None

        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._client = FrameClient(
            self._namespace, subscribe=True, timeout=wait_timeout_s
        )

    def _wait_for_transform_published(self, name, pose):
        frame_id = f'{self._namespace}_{name}'
        start_time = time.time()
        while True:
            try:
                pub_transform = self._tf_buffer.lookup_transform(
                    target_frame=self.pose_reference_frame,
                    source_frame=frame_id,
                    time=rospy.Time(0),
                )
                t = pub_transform.transform
                # float comparison is legitimate here since we use the same
                # conversion method in frame pub and here
                if (
                    t.translation.x == pose.position.x
                    and t.translation.y == pose.position.y
                    and t.translation.z == pose.position.z
                    and t.rotation.x == pose.orientation.x
                    and t.rotation.y == pose.orientation.y
                    and t.rotation.z == pose.orientation.z
                    and t.rotation.w == pose.orientation.w
                ):
                    break
            except (
                tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException,
            ):
                pass
            current_time = time.time()
            delta = current_time - start_time
            if delta >= self.TF_WAIT_TIMEOUT_S:
                return False
            time.sleep(self.TF_SYNC_TIME_S)
        return True

    @property
    def frames(self):
        return self._client.frames

    @property
    def active_frame(self):
        return self._client.active_frame

    @property
    def active_frame_frame(self):
        return self._client.active_frame_frame

    @property
    def tf_buffer(self):
        return self._tf_buffer

    def shutdown(self):
        if self._tf_listener:
            self._tf_listener.unregister()
        self._client.stop()

    def set_frame(self, name, pose, frame=None, temporary=False):
        if pose is None:
            self._client.delete_frame(name, temporary=temporary)
            self._client.update_frame('', temporary=temporary)
            return

        if frame:
            transform = self.get_transform(frame)
            if transform:
                ros_pose = tf2_geometry_msgs.do_transform_pose(
                    PoseStamped(pose=pose.to_ros_pose()), transform
                )
                pose = Pose.from_ros_pose(ros_pose)
        self._client.set_frame(name, pose.to_list(), temporary=temporary)
        self._client.update_frame(name, temporary=temporary)
        if not self._wait_for_transform_published(name, pose.to_ros_pose()):
            raise RuntimeError(f'Could not set frame {name}')

    def get_frame(self, name):
        frame = self.frames.get(name, None)
        if not frame:
            return None
        pose = frame.get('pose', None)
        if pose:
            return Pose.from_list(pose)
        else:
            return None

    def change_frame(self, name):
        self._client.change_frame(name)

    def get_transform(self, name, inverse=False):
        frame_id = f'{self._namespace}_{name}'
        target = self.pose_reference_frame
        source = frame_id
        if inverse:
            target, source = source, target

        try:
            return self._tf_buffer.lookup_transform(
                target_frame=target, source_frame=source, time=rospy.Time(0)
            )
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ):
            rospy.logwarn(f'Could not find transform for {frame_id}')
            return None


class UserFrameInterface(FrameInterface):
    def __init__(self, tf_buffer=None):
        pose_reference_frame = rospy.get_param(
            'moveit/pose_reference_frame', None
        )
        super().__init__(
            namespace='user_frames',
            pose_reference_frame=pose_reference_frame,
            tf_buffer=tf_buffer,
        )


class ToolFrameInterface(FrameInterface):
    def __init__(self, tf_buffer=None):
        pose_reference_frame = rospy.get_param(
            'moveit/tool_reference_frame', None
        )
        super().__init__(
            namespace='tool_frames',
            pose_reference_frame=pose_reference_frame,
            tf_buffer=tf_buffer,
        )


class UserFrameInterfaceSingleton:
    """
    Singleton interface to user frames
    """

    _instance = None

    def __init__(self, tf_buffer=None):
        if not UserFrameInterfaceSingleton._instance:
            UserFrameInterfaceSingleton._instance = UserFrameInterface(
                tf_buffer=tf_buffer
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)


class ToolFrameInterfaceSingleton:
    """
    Singleton interface to tool frames
    """

    _instance = None

    def __init__(self, tf_buffer=None):
        if not ToolFrameInterfaceSingleton._instance:
            ToolFrameInterfaceSingleton._instance = ToolFrameInterface(
                tf_buffer=tf_buffer
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)

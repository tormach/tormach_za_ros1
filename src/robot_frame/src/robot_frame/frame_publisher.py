from collections import namedtuple
from threading import Lock

import rospy
import tf2_ros
from tf.transformations import quaternion_from_euler

from geometry_msgs.msg import TransformStamped

import redis_store
from robot_frame_msgs.srv import UpdateFrame, UpdateFrameResponse
from std_msgs.msg import String

FrameItem = namedtuple('FrameItem', 'pose transform')


class FramePublisher:
    DEFAULT_PUBLISH_INTERVAL_S = 0.1
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(
        self,
        namespace,
        pose_reference_frame,
        publish_interval_s=DEFAULT_PUBLISH_INTERVAL_S,
        cache_tfs=False,
    ):
        self._frames = {}
        self._tmp_frames = {}
        self._active_frame = ''
        self._publish_interval_s = publish_interval_s
        self._namespace = namespace
        self._frame_lock = Lock()

        self._tf_broadcaster = tf2_ros.TransformBroadcaster()
        self._pose_reference_frame = pose_reference_frame
        self._cache_tfs = cache_tfs
        if self._cache_tfs:
            self._transforms = {}

        self._publish_timer = rospy.Timer(
            rospy.Duration.from_sec(self._publish_interval_s),
            self._on_publish_timer_tick,
        )

        self._change_srv = rospy.Service(
            f'{namespace}/change', UpdateFrame, self._change_frame
        )
        self._update_srv = rospy.Service(
            f'{namespace}/update', UpdateFrame, self._update_frame
        )
        self._active_pub = rospy.Publisher(
            f'{namespace}/active', String, latch=True, queue_size=1
        )
        self._active_frame_pub = rospy.Publisher(
            f'{namespace}/active_frame',
            String,
            latch=True,
            queue_size=1,
        )
        self._config = redis_store.ConfigClient(subscribe=True)
        self._config.on_update_received.append(self._on_config_update_received)
        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._config.wait_for_service(timeout=wait_timeout_s)
        self._load_frames(temporary=False)
        self._publish_active_frame()

    def stop(self):
        self._publish_timer.shutdown()
        self._config.stop()

    def _load_frames(self, temporary):
        if temporary:
            frames = self._tmp_frames
            namespace = f'{self._namespace}_tmp'
        else:
            frames = self._frames
            namespace = self._namespace
        rospy.logdebug(f"Updating frames {namespace}")
        frames.clear()
        data = self._config.get_param(namespace)
        if not isinstance(data, dict):
            if data is not None:
                rospy.logerr(f"Cannot load frame data from {namespace}")
            return

        for name, item in data.items():
            try:
                pose = item if temporary else item['pose']
                x, y, z, a, b, c = pose
            except (TypeError, ValueError, KeyError):
                rospy.logwarn(f"Cannot unpack frame {name}, ignoring value.")
                continue
            q = quaternion_from_euler(a, b, c, axes='sxyz')
            t = TransformStamped()
            t.transform.translation.x = x
            t.transform.translation.y = y
            t.transform.translation.z = z
            t.transform.rotation.x = q[0]
            t.transform.rotation.y = q[1]
            t.transform.rotation.z = q[2]
            t.transform.rotation.w = q[3]
            frames[name] = FrameItem(pose, t)

        rospy.logdebug(f"Found {len(data)} frames.")

    def _publish_frames(self):
        tfs = []
        stamp = rospy.Time.now()
        for name in self._frames.keys():
            for tf in self._publish_frame(
                self._frames, name, stamp, send=False
            ):
                tfs.append(tf)
        for name in self._tmp_frames.keys():
            for tf in self._publish_frame(
                self._tmp_frames, name, stamp, send=False
            ):
                tfs.append(tf)
        if self._cache_tfs:
            covered = set()
            for tf in tfs:
                self._transforms[tf.child_frame_id] = tf
                covered.add(tf.child_frame_id)
            for child_frame_id in set(self._transforms.keys()) - covered:
                self._transforms[child_frame_id].header.stamp = stamp
            self._tf_broadcaster.sendTransform(list(self._transforms.values()))
        else:
            self._tf_broadcaster.sendTransform(tfs)

    def _publish_frame(self, frames, name, stamp=None, send=True):
        item = frames[name]
        t = item.transform
        t.header.stamp = rospy.Time.now() if stamp is None else stamp
        t.header.frame_id = self._pose_reference_frame
        t.child_frame_id = self._compose_frame_id(name)
        if send:
            self._tf_broadcaster.sendTransform(t)
        else:
            yield t

    def _compose_frame_id(self, name):
        return f'{self._namespace}_{name}'

    def _publish_active_frame(self):
        if self._active_frame:
            frame_id = self._compose_frame_id(self._active_frame)
        else:
            frame_id = self._pose_reference_frame
        self._active_pub.publish(String(self._active_frame))
        self._active_frame_pub.publish(String(frame_id))

    def _change_frame(self, req):
        self._active_frame = req.name
        self._publish_active_frame()
        rospy.logdebug(f"Changed active frame {self._active_frame}")
        return UpdateFrameResponse(success=True)

    def _update_frame(self, req):
        with self._frame_lock:
            self._load_frames(temporary=req.temporary)
            frames = self._tmp_frames if req.temporary else self._frames
            if req.name and req.name in frames:
                self._publish_frame(frames, req.name)
                rospy.logdebug(f"Updated frame {req.name}")
                return UpdateFrameResponse(success=True)
            else:
                rospy.logdebug(
                    f"Frame {req.name} does not exist. Cannot update."
                )
                return UpdateFrameResponse(success=False)

    def _on_config_update_received(self, key, _value):
        if not key.startswith(self._namespace):
            return
        with self._frame_lock:
            self._load_frames(temporary=False)
            self._publish_frames()

    def _on_publish_timer_tick(self, _event=None):
        with self._frame_lock:
            self._publish_frames()

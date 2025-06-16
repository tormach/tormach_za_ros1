import time

import rospy

import redis_store
from robot_frame_msgs.srv import UpdateFrame, UpdateFrameRequest
from std_msgs.msg import String


class FrameClient:
    DEFAULT_SERVICE_TIMEOUT_S = 10.0
    UPDATE_TIMEOUT_S = 10.0
    WAIT_INTERVAL_S = 0.01

    def __init__(
        self, namespace, subscribe=False, timeout=DEFAULT_SERVICE_TIMEOUT_S
    ):
        self.frames_changed = []
        self.active_frame_changed = []
        self.active_frame_frame_changed = []
        self._namespace = namespace
        self._active_frame = ''
        self._active_frame_frame = ''
        self._frames = {}
        self._subscribed = subscribe
        self._active_frame_updated = False

        self._change_frame_srv = rospy.ServiceProxy(
            f'{namespace}/change', UpdateFrame
        )
        self._update_frame_srv = rospy.ServiceProxy(
            f'{namespace}/update', UpdateFrame
        )
        self._subs = []
        active_topic = f'{namespace}/active'
        active_frame_topic = f'{namespace}/active_frame'
        if subscribe:
            self._subs.append(
                rospy.Subscriber(
                    active_topic, String, self._on_active_update_received
                )
            )
            self._subs.append(
                rospy.Subscriber(
                    active_frame_topic,
                    String,
                    self._on_active_frame_update_received,
                )
            )
        else:
            message = rospy.wait_for_message(
                active_topic, String, timeout=timeout
            )
            self._active_frame = message.data
            message = rospy.wait_for_message(
                active_frame_topic,
                String,
                timeout=timeout,
            )
            self._active_frame_frame = message.data

        self._config = redis_store.ConfigClient(subscribe=subscribe)
        self._config.on_update_received.append(self._on_config_update_received)
        self._config.wait_for_service(timeout=timeout)
        if subscribe:
            self._update_frames()

    @property
    def active_frame(self):
        return self._active_frame

    @property
    def active_frame_frame(self):
        return self._active_frame_frame

    @property
    def frames(self):
        if self._subscribed:
            return self._frames

        data = self._config.get_param(self._namespace)
        frames = {}
        self._load_frame_data(frames, data)
        return frames

    def stop(self):
        for sub in self._subs:
            sub.unregister()
        self._config.stop()

    def change_frame(self, name):
        self._active_frame_updated = False
        self._change_frame_srv(UpdateFrameRequest(name=name, temporary=False))
        if not self._subscribed:
            return
        start_time = time.time()
        while not self._active_frame_updated:
            rospy.sleep(rospy.Duration.from_sec(self.WAIT_INTERVAL_S))
            current_time = time.time()
            runtime = current_time - start_time
            if runtime >= self.UPDATE_TIMEOUT_S:
                rospy.logerr('Did not receive active frame update.')
                break

    def set_frame(self, name, pose, data=None, temporary=False):
        if self._subscribed and name in self._frames:
            current = self._frames.get(name, {})
            old_data = current.get('data', {}).copy()
        else:
            old_data = {}
        if data is not None:
            old_data.update(data)
        data = old_data
        if not temporary:
            key = f'{self._namespace}/{name}'
            self._config.set_param(key, {'pose': pose, 'data': data})
        else:
            key = f'{self._namespace}_tmp/{name}'
            rospy.set_param(key, pose)

    def delete_frame(self, name, temporary=False):
        if not temporary:
            key = f'{self._namespace}/{name}'
            self._config.delete_param(key)
        else:
            key = f'{self._namespace}_tmp/{name}'
            rospy.delete_param(key)
        if self._active_frame == name:
            self._change_frame_srv(UpdateFrameRequest(name='', temporary=False))

    def update_frame(self, name, temporary=False):
        self._update_frame_srv(
            UpdateFrameRequest(name=name, temporary=temporary)
        )

    def clear_frames(self):
        self._config.delete_param(self._namespace)
        try:
            rospy.delete_param(f'{self._namespace}_tmp')
        except KeyError:
            pass

    def _update_frames(self):
        data = self._config.get_param(self._namespace)
        self._load_frame_data(self._frames, data)

    def _load_frame_data(self, frames, data):
        frames.clear()
        if data is None:
            return
        if not isinstance(data, dict):
            rospy.logerr(f"Cannot load frame data from {self._namespace}")
            return
        for name, item in data.items():
            try:
                pose = item['pose']
                if 'data' not in item:
                    item['data'] = {}
                item_data = item['data']
                if (
                    not isinstance(pose, list)
                    or len(pose) != 6
                    or not isinstance(item_data, dict)
                ):
                    raise KeyError()
            except (KeyError, TypeError):
                rospy.logwarn(f"Cannot unpack frame {name}, ignoring value.")
                continue
            frames[name] = item

    def _on_active_update_received(self, msg):
        self._active_frame = msg.data
        self._active_frame_updated = True
        for f in self.active_frame_changed:
            f(msg.data)

    def _on_active_frame_update_received(self, msg):
        self._active_frame_frame = msg.data
        for f in self.active_frame_frame_changed:
            f(self._active_frame_frame)

    def _on_config_update_received(self, key, _value):
        if key.startswith(self._namespace):
            self._update_frames()
            for f in self.frames_changed:
                f()

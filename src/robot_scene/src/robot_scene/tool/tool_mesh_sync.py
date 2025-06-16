from threading import Lock

import rospy

from robot_frame import FrameClient
from ..robot_description import (
    RobotDescription,
    RobotDescriptionReadError,
)
from .scene_transform_updater import SceneTransformUpdater


class ToolMeshSync:
    NO_TOOL = ''
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(
        self,
        update_interval_s,
        tool_urdfs,
        tool_attach_link,
        tool_touch_links,
        namespace='tool_frames',
    ):
        self._update_interval_s = update_interval_s
        self._tool_urdfs = tool_urdfs
        self._tool_attach_link = tool_attach_link
        self._tool_touch_links = tool_touch_links
        self._namespace = namespace
        self._update_timer = None
        self._update_lock = Lock()
        self._scene_tf_updater = None
        self._client = None
        self._tool = self.NO_TOOL
        self._previous_tool = self.NO_TOOL
        self._subs = []
        self._descriptions = {
            name: RobotDescription(
                namespace=f'{name}_', base_link=self._tool_attach_link
            )
            for name in tool_urdfs.keys()
        }

    def start(self):
        self._scene_tf_updater = SceneTransformUpdater(
            tool_attach_link=self._tool_attach_link,
            tool_touch_links=self._tool_touch_links,
        )
        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._client = FrameClient(
            self._namespace, subscribe=True, timeout=wait_timeout_s
        )
        self._client.active_frame_changed.append(self._on_frames_updated)
        self._client.frames_changed.append(self._on_frames_updated)
        self._update_timer = rospy.Timer(
            rospy.Duration.from_sec(self._update_interval_s), self._update
        )

    def stop(self):
        if self._update_timer:
            self._update_timer.shutdown()
            self._update_timer = None
        if self._tool != self.NO_TOOL and self._tool in self._descriptions:
            description = self._descriptions[self._tool]
            if description.initialized:
                self._scene_tf_updater.remove_robot(description)
        if self._client:
            self._client.stop()
            self._client = None
        if self._scene_tf_updater:
            self._scene_tf_updater.stop()
            self._scene_tf_updater = None

    def _on_frames_updated(self, _=None):
        with self._update_lock:
            if self._client:
                active_frame = self._client.active_frame
                frame = self._client.frames.get(active_frame, {})
                new_tool = frame.get('data', {}).get('model_type', '')
            else:
                new_tool = ''
            if self._tool == new_tool:
                return
            self._previous_tool = self._tool
            self._tool = new_tool
        self._update()

    def _update(self, _event=None):
        with self._update_lock:
            self._update_locked()

    def _update_locked(self):
        changed = self._previous_tool != self._tool
        if changed:
            if self._previous_tool in self._descriptions:
                description = self._descriptions[self._previous_tool]
                if description.initialized:
                    self._scene_tf_updater.remove_robot(description)
            self._previous_tool = self._tool

        if self._tool == self.NO_TOOL:
            return

        if self._tool not in self._descriptions:
            rospy.logerr(f"No machine URDF for tool type {self._tool} defined.")
            return

        description = self._descriptions[self._tool]
        if not description.initialized:
            urdf_file = self._tool_urdfs[self._tool]
            try:
                description.read_from_xacro(urdf_file)
            except RobotDescriptionReadError as e:
                rospy.logwarn(f"Error reading URDF file {urdf_file}: {e}")
                return
            rospy.loginfo(f"Loading tool models for {self._tool}")

        if changed:
            self._scene_tf_updater.add_robot(description)
        else:
            self._scene_tf_updater.update_robot(description)

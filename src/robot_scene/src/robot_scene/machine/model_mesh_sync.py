from threading import Lock

import rospy

from ros_machinetalk import (
    InstanceClient,
    StatusSubscriber,
)
from ..robot_description import (
    RobotDescription,
    RobotDescriptionReadError,
)
from .scene_transform_updater import SceneTransformUpdater


class ModelMeshSync:
    def __init__(self, update_interval_s, machine_urdfs):
        self._update_interval_s = update_interval_s
        self._machine_urdfs = machine_urdfs
        self._instance_client = None
        self._update_timer = None
        self._scene_tf_updater = None
        self._status_subs = {}
        self._descriptions = {}
        self._has_load_error = {}
        self._nodes = {}
        self._update_lock = Lock()

    def start(self):
        self._instance_client = InstanceClient()
        self._instance_client.on_node_added.append(self._on_node_added)
        self._instance_client.on_node_removed.append(self._on_node_removed)
        self._instance_client.on_node_updated.append(self._on_node_updated)
        self._add_all_nodes()

        self._update_timer = rospy.Timer(
            rospy.Duration.from_sec(self._update_interval_s), self._update
        )

        self._scene_tf_updater = SceneTransformUpdater()

    def stop(self):
        if self._instance_client:
            self._instance_client.stop()
            self._instance_client = None
        if self._update_timer:
            self._update_timer.shutdown()
            self._update_timer = None
        for uuid, node in list(self._nodes.items()):
            status = self._status_subs[uuid]
            status.stop()
            description = self._descriptions.pop(uuid)
            self._nodes.pop(uuid)
            self._has_load_error.pop(uuid)
            if description.initialized:
                self._scene_tf_updater.remove_robot(description)
        if self._scene_tf_updater:
            self._scene_tf_updater.stop()
            self._scene_tf_updater = None

    def _update(self, _event=None):
        with self._update_lock:
            self._update_locked()

    def _update_locked(self):
        for uuid, node in list(self._nodes.items()):
            status = self._status_subs[uuid]
            description = self._descriptions[uuid]
            if not (status.config and status.motion):
                return

            if self._has_load_error[uuid]:
                return

            if not description.initialized:
                name = status.config.name
                if name not in self._machine_urdfs:
                    self._has_load_error[uuid] = True
                    rospy.logwarn(f"No machine URDF for {name} defined.")
                    continue
                urdf_file = self._machine_urdfs[name]
                try:
                    description.read_from_xacro(urdf_file)
                except RobotDescriptionReadError as e:
                    self._has_load_error[uuid] = True
                    rospy.logwarn(f"Error reading URDF file {urdf_file}: {e}")
                    continue
                rospy.loginfo(
                    f"Loading {name} machine models for {node['name']}"
                )
                self._scene_tf_updater.add_robot(description, status, node)
            else:
                self._scene_tf_updater.update_robot(description, status, node)

    def _add_all_nodes(self):
        for node in self._instance_client.nodes:
            self._on_node_added(node)

    def _on_node_added(self, node):
        uuid = node['uuid']
        with self._update_lock:
            self._nodes[uuid] = node
            rospy.logdebug(f"node added {uuid}")
            self._status_subs[uuid] = StatusSubscriber(uuid)
            self._descriptions[uuid] = RobotDescription(namespace=f'{uuid}_')
            self._has_load_error[uuid] = False
        self._update()

    def _on_node_removed(self, node):
        uuid = node['uuid']
        with self._update_lock:
            self._nodes.pop(uuid)
            rospy.logdebug(f"node removed {uuid}")
            status_sub = self._status_subs.pop(uuid)
            status_sub.stop()
            description = self._descriptions.pop(uuid)
            if description.initialized:
                self._scene_tf_updater.remove_robot(description)
            self._has_load_error.pop(uuid)
        self._update()

    def _on_node_updated(self, node):
        uuid = node['uuid']
        with self._update_lock:
            self._nodes[uuid] = node
        self._update()

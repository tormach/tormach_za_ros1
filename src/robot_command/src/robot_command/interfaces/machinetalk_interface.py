from functools import partial
from machinetalk.protobuf.status_pb2 import (
    EMC_TASK_STATE_ON,
    EMC_TASK_MODE_AUTO,
    EMC_TASK_MODE_MDI,
    EMC_TASK_INTERP_IDLE,
)

import rospy

from ros_machinetalk import (
    CommandClient,
    InstanceClient,
    ConnectedSubscriber,
    StatusSubscriber,
)
from ros_machinetalk_msgs.msg import CommandGoal


class MachinetalkInstanceNotFoundError(Exception):
    def __init__(self, instance):
        self.instance = instance


class MachinetalkInstanceNotConnectedError(Exception):
    def __init__(self, instance):
        self.instance = instance


class MachinetalkInterface:
    def __init__(self):
        self._instance_client = InstanceClient()
        self._instance_client.on_node_added.append(self._on_node_added)
        self._instance_client.on_node_removed.append(self._on_node_removed)
        self._instance_client.on_node_updated.append(self._on_node_updated)

        self._cmd_clients = {}
        self._status_subs = {}
        self._connected_subs = {}
        self._uuid_by_name = {}

        # Callbacks called when connected state of a node changes,
        # arguments: state and uuid
        self.on_connected_changed = []

        self._add_all_nodes()

    @property
    def instance_client(self):
        return self._instance_client

    @property
    def command_clients(self):
        return self._cmd_clients

    @property
    def connected_subscribers(self):
        return self._connected_subs

    @property
    def status_subscribers(self):
        return self._status_subs

    def shutdown(self):
        for client in self._cmd_clients.values():
            client.stop()
        for sub in self._connected_subs.values():
            sub.stop()
        for sub in self._status_subs.values():
            sub.stop()
        self._instance_client.stop()

    def execute_mdi(self, command, instance=None):
        uuid = self._get_instance_by_name_or_default(instance)
        self._check_connected(instance, uuid)
        self._cmd_clients[uuid].set_task_mode(CommandGoal.TASK_MODE_MDI)
        self._cmd_clients[uuid].execute_mdi(command)

    def cycle_start(self, instance=None):
        uuid = self._get_instance_by_name_or_default(instance)
        self._check_connected(instance, uuid)
        self._cmd_clients[uuid].set_task_mode(CommandGoal.TASK_MODE_AUTO)
        self._cmd_clients[uuid].run_program(0, 'execute')

    def abort(self, instance=None):
        uuid = self._get_instance_by_name_or_default(instance)
        self._check_connected(instance, uuid)
        self._cmd_clients[uuid].abort('execute')

    def is_connected(self, instance=None, uuid=None):
        if not uuid:
            uuid = self._get_instance_by_name_or_default(instance)
        return self._connected_subs[uuid].connected

    def get_machine_state(self, instance=None):
        uuid = self._get_instance_by_name_or_default(instance)
        if not self.is_connected(uuid=uuid):
            return 'disconnected'
        status_sub = self._status_subs[uuid]
        if not status_sub.synced:
            return 'disconnected'
        # now check the status
        estop = status_sub.task.task_state != EMC_TASK_STATE_ON
        running = (
            status_sub.task.task_mode in (EMC_TASK_MODE_AUTO, EMC_TASK_MODE_MDI)
            and status_sub.interp.interp_state != EMC_TASK_INTERP_IDLE
        )

        program_loaded = (
            'very-unlikely-pathpilot-gcode.file' in status_sub.task.file
            or (
                status_sub.task.file != ""
                and status_sub.config.remote_path in status_sub.task.file
            )
        )
        if estop:
            return 'estop'
        elif running:
            return 'running'
        elif program_loaded:
            return 'ready'
        else:
            return 'idle'

    def get_status(self, instance=None):
        uuid = self._get_instance_by_name_or_default(instance)
        self._check_connected(instance, uuid)
        return self._status_subs[uuid]

    def update_pose(self, pose, instance=None):
        uuid = self._get_instance_by_name_or_default(instance)
        name = ''
        for node in self._instance_client.nodes:
            if node.get('uuid', None) == uuid:
                name = node.get('name', '')
        self._instance_client.update_node(name, uuid, pose)

    def _on_connected_changed(self, connected, uuid):
        rospy.loginfo(f'Machinetalk node {uuid} connected {connected}')
        for cb in self.on_connected_changed:
            cb(connected, uuid)

    def _add_all_nodes(self):
        for node in self._instance_client.nodes:
            self._on_node_added(node)

    def _on_node_added(self, node):
        uuid = node['uuid']
        rospy.loginfo(f'node added {uuid}')
        self._cmd_clients[uuid] = CommandClient(uuid)
        connected_sub = ConnectedSubscriber(uuid)
        connected_sub.on_connected_changed.append(
            partial(self._on_connected_changed, uuid=uuid)
        )
        self._connected_subs[uuid] = connected_sub
        self._status_subs[uuid] = StatusSubscriber(uuid)

        self._uuid_by_name[node['name']] = uuid

    def _on_node_removed(self, node):
        uuid = node['uuid']
        rospy.loginfo(f'node removed {uuid}')
        cmd_client = self._cmd_clients.pop(uuid)
        cmd_client.stop()
        connected_sub = self._connected_subs.pop(uuid)
        connected_sub.stop()
        status_sub = self._status_subs.pop(uuid)
        status_sub.stop()
        del self._uuid_by_name[node['name']]

    def _on_node_updated(self, node):
        rospy.loginfo('node updated {}'.format(node['uuid']))
        for name, node_ in self._uuid_by_name.items():
            if node_ == node['uuid']:
                del self._uuid_by_name[name]
                break
        self._uuid_by_name[node['name']] = node['uuid']

    def _get_instance_by_name_or_default(self, name):
        if not name:
            uuid = InstanceClient.get_default_uuid()
        else:
            uuid = self._uuid_by_name.get(name, None)
        if not uuid:
            raise MachinetalkInstanceNotFoundError(name)
        return uuid

    def _check_connected(self, instance, uuid):
        if not self.is_connected(uuid=uuid):
            raise MachinetalkInstanceNotConnectedError(instance)


class MachinetalkInterfaceSingleton:
    """
    Singleton interface class to ros_machinetalk.
    """

    _instance = None

    def __init__(self):
        if not MachinetalkInterfaceSingleton._instance:
            MachinetalkInterfaceSingleton._instance = MachinetalkInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

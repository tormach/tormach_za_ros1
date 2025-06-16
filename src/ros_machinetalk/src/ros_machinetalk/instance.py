import shlex
from subprocess import Popen

import rospy
from ros_machinetalk_msgs.msg import Instance, Instances
from ros_machinetalk_msgs.srv import AddUpdateNode, RemoveNode
from pymachinetalk.dns_sd import ServiceDiscovery, Service
from redis_store import ConfigClient


class InstanceBase:
    _ADD_NODE_ACTION_NAME = 'machinetalk/add_node'
    _UPDATE_NODE_ACTION_NAME = 'machinetalk/update_node'
    _REMOVE_NODE_ACTION_NAME = 'machinetalk/remove_node'
    _INSTANCES_TOPIC_NAME = 'machinetalk/instances'
    _NODES_PARAM_NAME = 'machinetalk/nodes'


class InstanceServer(InstanceBase):
    def __init__(self):
        self._config = ConfigClient(subscribe=True)
        self._config.on_update_received.append(self._on_config_update)
        self._machinetalk_nodes = {}

        self._sd = ServiceDiscovery()
        self._service = Service(type_='launcher')
        self._sd.register(self._service)
        self._service.on_service_infos_updated.append(self._on_services_updated)

        self._pub = rospy.Publisher(
            self._INSTANCES_TOPIC_NAME, Instances, queue_size=1, latch=True
        )
        self._add_node = rospy.Service(
            self._ADD_NODE_ACTION_NAME, AddUpdateNode, self._add_node_srv_cb
        )
        self._update_node = rospy.Service(
            self._UPDATE_NODE_ACTION_NAME,
            AddUpdateNode,
            self._update_node_srv_cb,
        )
        self._remove_node = rospy.Service(
            self._REMOVE_NODE_ACTION_NAME, RemoveNode, self._remove_node_srv_cb
        )

    def start(self):
        self._sd.start()
        self._start_stop_nodes()

    def stop(self):
        self._pub.publish(Instances())
        self._stop_all_nodes()
        self._sd.stop()

    def _on_services_updated(self):
        infos = self._service.service_infos
        rospy.loginfo(f'{len(infos)} instances found')
        instances = Instances()
        for info in infos:
            instance = self._service_info_to_instance(info)
            instances.instances.append(instance)
            rospy.loginfo(instance.name)
        self._pub.publish(instances)

    @staticmethod
    def _service_info_to_instance(info):
        raw_name = info.name
        name = raw_name[0 : raw_name.rindex('._machinekit._tcp.local.')]
        return Instance(
            uuid=info.properties.get(b'uuid', b'').decode(),
            name=name,
            version=info.properties.get(b'version', b'').decode(),
            host_name=info.server,
        )

    def _on_config_update(self, param, _value):
        if param == self._NODES_PARAM_NAME:
            self._start_stop_nodes()

    def _add_node_srv_cb(self, req):
        nodes = rospy.get_param(self._NODES_PARAM_NAME, [])
        for node in nodes:
            if node['uuid'] == req.uuid:
                rospy.logwarn(f'adding node {req.uuid} failed, already exists')
                return False
        nodes.append({'name': req.name, 'uuid': req.uuid, 'pose': req.pose})
        rospy.loginfo(f'adding node {req.uuid}')
        self._config.set_param(self._NODES_PARAM_NAME, nodes)
        return True

    def _update_node_srv_cb(self, req):
        nodes = rospy.get_param(self._NODES_PARAM_NAME, [])
        found = False
        for node in nodes:
            if node['uuid'] == req.uuid:
                node['name'] = req.name
                node['pose'] = req.pose
                found = True
        if not found:
            rospy.logwarn(f'updating node {req.uuid} failed')
            return False
        rospy.loginfo(f'updating node {req.uuid}')
        self._config.set_param(self._NODES_PARAM_NAME, nodes)
        return True

    def _remove_node_srv_cb(self, req):
        nodes = rospy.get_param(self._NODES_PARAM_NAME, [])
        found = False
        for node in nodes:
            if node['uuid'] == req.uuid:
                nodes.remove(node)
                found = True
                break
        if found:
            rospy.loginfo(f'removing node {req.uuid}')
            self._config.set_param(self._NODES_PARAM_NAME, nodes)
        else:
            rospy.logwarn(f'removing node {req.uuid} failed')
        return found

    def _start_stop_nodes(self):
        nodes = rospy.get_param(self._NODES_PARAM_NAME, [])
        new_uuids = {srv['uuid'] for srv in nodes}
        old_uuids = set(self._machinetalk_nodes.keys())

        added_uuids = new_uuids - old_uuids
        removed_uuids = old_uuids - new_uuids

        for uuid in removed_uuids:
            self._stop_machinetalk_node(uuid)
        for uuid in added_uuids:
            self._start_machinetalk_node(uuid)

    def _start_machinetalk_node(self, uuid):
        process = Popen(
            shlex.split(
                'roslaunch ros_machinetalk machinetalk_node.launch uuid:={}'.format(
                    uuid
                )
            )
        )
        self._machinetalk_nodes[uuid] = process

    def _stop_machinetalk_node(self, uuid):
        process = self._machinetalk_nodes.get(uuid, None)
        if process:
            process.terminate()
        del self._machinetalk_nodes[uuid]

    def _stop_all_nodes(self):
        for uuid in list(self._machinetalk_nodes.keys()):
            self._stop_machinetalk_node(uuid)
        self._machinetalk_nodes = {}


class InstanceClient(InstanceBase):
    def __init__(self):
        # Callback called when instances are changed
        self.on_instances_changed = []
        # Callback called when a new node has been added, node as argument
        self.on_node_added = []
        # Callback called when an existing node has been removed, node as argument
        self.on_node_removed = []
        # Callback called when an existing node has been updated, node as argument
        self.on_node_updated = []
        # Callback called when nodes are changed
        self.on_nodes_changed = []

        self._sub = rospy.Subscriber(
            self._INSTANCES_TOPIC_NAME,
            Instances,
            self._on_instances_update_received,
        )
        self._add_node_srv = rospy.ServiceProxy(
            self._ADD_NODE_ACTION_NAME, AddUpdateNode
        )
        self._update_node_srv = rospy.ServiceProxy(
            self._UPDATE_NODE_ACTION_NAME, AddUpdateNode
        )
        self._remove_node_srv = rospy.ServiceProxy(
            self._REMOVE_NODE_ACTION_NAME, RemoveNode
        )

        self._config = ConfigClient(subscribe=True)
        self._config.on_update_received.append(self._on_config_update_received)

        self._instances = []
        self._nodes = rospy.get_param(self._NODES_PARAM_NAME, [])

    @property
    def instances(self):
        return self._instances

    @property
    def nodes(self):
        return self._nodes

    def add_node(self, name, uuid, pose):
        return self._add_node_srv.call(name, uuid, pose)

    def update_node(self, name, uuid, pose):
        return self._update_node_srv.call(name, uuid, pose)

    def remove_node(self, uuid):
        return self._remove_node_srv.call(uuid)

    def stop(self):
        self._sub.unregister()
        self._config.stop()

    @staticmethod
    def get_default_uuid():
        nodes = rospy.get_param(InstanceBase._NODES_PARAM_NAME, [])
        if len(nodes) == 0:
            return None
        return nodes[0].get('uuid', None)

    def _on_instances_update_received(self, msg):
        self._instances = msg.instances
        for cb in self.on_instances_changed:
            cb()

    def _on_config_update_received(self, key, value):
        if key != self._NODES_PARAM_NAME:
            return

        nodes = value
        new_nodes_by_uuid = {node['uuid']: node for node in nodes}
        old_nodes_by_uuid = {node['uuid']: node for node in self._nodes}
        new_uuids = set(new_nodes_by_uuid.keys())
        old_uuids = set(old_nodes_by_uuid.keys())

        added_uuids = new_uuids - old_uuids
        removed_uuids = old_uuids - new_uuids
        recurring_uuids = new_uuids - removed_uuids

        for uuid in removed_uuids:
            for cb in self.on_node_removed:
                cb(old_nodes_by_uuid[uuid])
        for uuid in added_uuids:
            for cb in self.on_node_added:
                cb(new_nodes_by_uuid[uuid])
        for uuid in recurring_uuids:
            for old_node in self._nodes:
                if old_node['uuid'] != uuid:
                    continue
                for new_node in nodes:
                    if new_node['uuid'] != uuid:
                        continue
                    if new_node != old_node:
                        for cb in self.on_node_updated:
                            cb(new_node)
        self._nodes = nodes
        for cb in self.on_nodes_changed:
            cb()

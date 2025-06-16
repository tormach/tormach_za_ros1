import copy
from redis_store import ConfigClient

from .waypoint import Waypoint, TargetType
from .waypoints import Waypoints


class GlobalWaypoints(Waypoints):
    """Provides a high level interface to global waypoints"""

    NAMESPACE = 'global_waypoints/'

    def __init__(self, waypoints=None, subscribe=False):
        super().__init__(waypoints)
        self._config = ConfigClient(subscribe=subscribe)
        if subscribe:
            self._config.on_update_received.append(self._on_update_received)

    def stop(self):
        self._config.stop()

    def copy_data_to(self, target):
        if not isinstance(target, GlobalWaypoints):
            raise TypeError('Can only copy data to other global waypoints.')

        new_waypoints = copy.deepcopy(self._waypoints)

        target.reset_data(waypoints=new_waypoints)

    def read_from_store(self):
        raw_waypoints = self._config.get_param(self.NAMESPACE)
        if raw_waypoints is None:
            raise ValueError('Reading waypoint parameters failed.')

        waypoints = [
            self._read_waypoint_param(key, raw_waypoints[key])
            for key in raw_waypoints
        ]
        self.reset_data(waypoints=waypoints)

    def write_to_store(self):
        waypoints = self._config.get_param(self.NAMESPACE)
        if waypoints is None:
            raise ValueError('Reading waypoint parameters failed.')

        old = set(waypoints.keys())
        for waypoint in self._waypoints:
            self._write_waypoint_param(
                namespace=self.NAMESPACE, waypoint=waypoint
            )
            if waypoint.name in old:
                old.remove(waypoint.name)
        for name in old:
            self._config.delete_param(self.NAMESPACE + name)

    def export_to_file(self, file_path):
        self._config.export_param(self.NAMESPACE, file_path)

    def import_from_file(self, file_path):
        self._config.import_param(self.NAMESPACE, file_path)

    def _write_waypoint_param(self, namespace, waypoint):
        type_map = {TargetType.Pose: 'POSE', TargetType.Joints: 'JOINTS'}
        param_name = namespace + waypoint.name
        param_value = [type_map[waypoint.target_type], waypoint.target]
        self._config.set_param(param_name, param_value)

    @staticmethod
    def _read_waypoint_param(name, value):
        try:
            if len(value) != 2:
                raise ValueError()
            target = value[1]

            if value[0] == 'POSE':
                target_type = TargetType.Pose
            elif value[0] == 'JOINTS':
                target_type = TargetType.Joints
            else:
                raise ValueError()
        except ValueError:
            raise ValueError(f'Global waypoint "{name}" not correctly defined.')

        return Waypoint(name=name, target=target, target_type=target_type)

    def _on_update_received(self, key, _value):
        if not key.startswith(self.NAMESPACE):
            return
        self.read_from_store()

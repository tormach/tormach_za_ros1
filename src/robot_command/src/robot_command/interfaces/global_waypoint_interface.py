from redis_store import ConfigClient
from ..rpl import Joints, Pose

GLOBAL_WAYPOINTS_NAMESPACE = 'global_waypoints/'


class GlobalWaypointInterface:
    def __init__(self):
        self._config = ConfigClient()

    def shutdown(self):
        self._config.stop()

    def get_global_waypoint(self, name):
        param_name = GLOBAL_WAYPOINTS_NAMESPACE + name

        value = self._config.get_param(param_name)
        if value is None:
            raise KeyError(f'Global waypoint "{name}" not found.')

        try:
            if len(value) != 2:
                raise ValueError()

            if value[0] == 'POSE':
                return Pose(*value[1]).with_units()
            elif value[0] == 'JOINTS':
                return Joints(*value[1]).with_units()
            else:
                raise ValueError()
        except ValueError:
            raise ValueError(f'Global waypont "{name}" not correctly defined.')

    def set_global_waypoint(self, name, value):
        param_name = GLOBAL_WAYPOINTS_NAMESPACE + name
        if not isinstance(value, (Pose, Joints)):
            raise TypeError('Pose or Joints type expected as value parameter.')
        type_map = {Pose: 'POSE', Joints: 'JOINTS'}

        param_value = [type_map[type(value)], value.to_list()]
        self._config.set_param(param_name, param_value)


class GlobalWaypointInterfaceSingleton:
    """
    Singleton interface to global waypoints.
    """

    _instance = None

    def __init__(self):
        if not GlobalWaypointInterfaceSingleton._instance:
            GlobalWaypointInterfaceSingleton._instance = (
                GlobalWaypointInterface()
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)

from .waypoint import Waypoint


class Waypoints:
    def __init__(self, waypoints=None):
        if waypoints is None:
            waypoints = []

        self._waypoints = waypoints
        self._uuid_waypoint_map = {}

        self._update_uuid_waypoint_map()

    def reset_data(self, waypoints=object):
        """
        :type waypoints: List[Waypoint]
        """
        if waypoints is not None:
            self._waypoints = waypoints
            self._update_uuid_waypoint_map()

    @property
    def waypoints(self):
        return self._waypoints

    def get_waypoint(self, uuid):
        return self._uuid_waypoint_map.get(uuid, None)

    def create_waypoint(self, uuid=None):
        """
        Creates a new waypoint and adds it to the waypoint list.
        :rtype: Waypoint
        """
        new_waypoint = Waypoint(uuid=uuid)
        self.waypoints.append(new_waypoint)
        self._uuid_waypoint_map[new_waypoint.uuid] = new_waypoint
        return new_waypoint

    def remove_waypoint(self, waypoint):
        """
        Removes a waypoint from the waypoint list.
        :type waypoint: Waypoint
        """
        self._verify_waypoint_exists(waypoint)

        self.waypoints.remove(waypoint)
        self._uuid_waypoint_map.pop(waypoint.uuid)

    def update_waypoint(self, waypoint, property_, value):
        """
        Updates a property of a waypoint with a new value.
        :type waypoint: Waypoint
        """
        self._verify_waypoint_exists(waypoint)

        if not hasattr(waypoint, property_):
            raise AttributeError(f'Waypoint has no property named {property_}')
        try:
            setattr(waypoint, property_, value)
        except AttributeError:
            raise AttributeError(
                f'Setting waypoint attribute {property_} failed'
            )

    def _verify_waypoint_exists(self, waypoint):
        if waypoint.uuid not in self._uuid_waypoint_map:
            raise KeyError('Waypoint is not part of this program')

    def _update_uuid_waypoint_map(self):
        if self._waypoints is None:
            self._uuid_waypoint_map = {}
        else:
            self._uuid_waypoint_map = {
                waypoint.uuid: waypoint for waypoint in self.waypoints
            }

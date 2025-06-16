import rospy
from redis import Redis
from .params_drive import EtherCATDriveParams


class EtherCATDriveRedisGUIDParams(EtherCATDriveParams):
    DRIVE_GUID_KEY = "drive_guids"

    def write_guid_to_redis(self, position, guid):
        self.redis.hset(self.DRIVE_GUID_KEY, position, guid)

    def read_guid_from_redis(self, position):
        if self.redis.hexists(self.DRIVE_GUID_KEY, position):
            return self.redis.hget(self.DRIVE_GUID_KEY, position)
        else:
            return None

    @property
    def redis(self):
        if not hasattr(self, "_redis"):
            # Copied from robot_ui/src/robot_ui/pathpilot/hub/hub_connector.py
            redis_host = rospy.get_param('redis_host', 'localhost')
            redis_port = rospy.get_param('redis_port', 6379)
            redis_db = rospy.get_param('~redis_db', 1)

            self._redis = Redis(host=redis_host, port=redis_port, db=redis_db)
        return self._redis

    def get_guid(self, position):
        guid = super().get_guid(position)
        if guid and self.read_guid_from_redis(position) != guid:
            self.write_guid_to_redis(position, guid)
        return guid

    def set_guid(self, position, **kwargs):
        super().set_guid(position, **kwargs)
        self.get_guid(position)

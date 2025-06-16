import rospy
from redis_store import ConfigClient


class ConfigInterface:
    USER_PREFIX = 'user_config'
    CUSTOM_USER_PREFIX = f'{USER_PREFIX}/custom'
    MACHINE_STATE_PREFIX = 'machine_state'

    def __init__(self):
        self._config = ConfigClient(subscribe=True)

    @property
    def linear_unit(self):
        return self._get_param_fast('linear_unit')

    @property
    def angular_unit(self):
        return self._get_param_fast('angular_unit')

    @property
    def time_unit(self):
        return self._get_param_fast('time_unit')

    @property
    def optional_stop(self):
        return self._get_param_fast('optional_stop')

    @property
    def blend_radius(self):
        return self._get_param_fast('blend_radius')

    def add_update_cb(self, cb):
        self._config.on_update_received.append(cb)

    def shutdown(self):
        self._config.stop()

    def get_base_param(self, name, default=None):
        result = self._config.get_param(name)
        return default if result is None else result

    def get_param(self, name, default=None):
        return self.get_base_param(f'{self.USER_PREFIX}/{name}', default)

    def set_base_param(self, name, value):
        self._config.set_param(name, value)
        self._config.save_param(name)

    def set_param(self, name, value):
        key = f'{self.USER_PREFIX}/{name}'
        self.set_base_param(key, value)

    def get_custom_param(self, name, default=None):
        key = f'{self.CUSTOM_USER_PREFIX}/{name}'
        return self.get_base_param(key, default)

    def set_custom_param(self, name, value):
        key = f'{self.CUSTOM_USER_PREFIX}/{name}'
        self.set_base_param(key, value)

    def delete_base_param(self, name):
        self._config.delete_param(name)

    def delete_custom_param(self, name):
        key = f'{self.CUSTOM_USER_PREFIX}/{name}'
        self.delete_base_param(key)

    def get_machine_param(self, name, default=None):
        key = f'{self.MACHINE_STATE_PREFIX}/{name}'
        return self.get_base_param(key, default)

    def set_machine_param(self, name, value):
        key = f'{self.MACHINE_STATE_PREFIX}/{name}'
        self.set_base_param(key, value)

    def _get_param_fast(self, name, default=None):
        return rospy.get_param(f'{self.USER_PREFIX}/{name}', default)


class ConfigInterfaceSingleton:
    """
    Singleton interface to configs.
    """

    _instance = None

    def __init__(self):
        if not ConfigInterfaceSingleton._instance:
            ConfigInterfaceSingleton._instance = ConfigInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

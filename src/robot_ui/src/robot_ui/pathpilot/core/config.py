import functools
import re
import sys

from redis_store import ConfigClient

import rospy
from PySide6.QtCore import QObject, Property, Slot
from PySide6.QtQml import QQmlPropertyMap, QmlElement, QmlSingleton, QJSValue

from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class Config(QObject):
    """Interface to user and application config."""

    DATA_CONFIG_PARAM = (
        'robot_ui_config'
        if sys.argv[0].endswith('robot_ui')
        else 'launcher_ui_config'
    )
    MACHINE_STATE_PARAM = 'machine_state'
    USER_CONFIG_PARAM = 'user_config'

    def __init__(self, parent=None):
        super().__init__(parent)

        self._data = self._config_property_map(
            self.DATA_CONFIG_PARAM, global_space=True, add_cb=False
        )
        self._machine = self._config_property_map(self.MACHINE_STATE_PARAM)
        self._user = self._config_property_map(self.USER_CONFIG_PARAM)

        self._config = ConfigClient(subscribe=True)
        self._config.on_update_received.append(self._on_update_received)
        ensure_cleanup(self._shutdown)

    @Property(QQmlPropertyMap, constant=True)
    def data(self):
        return self._data

    @Property(QQmlPropertyMap, constant=True)
    def user(self):
        return self._user

    @Property(QQmlPropertyMap, constant=True)
    def machine(self):
        return self._machine

    def _config_property_map(self, param_key, global_space=False, add_cb=True):
        property_map = QQmlPropertyMap(self)
        update_base = None if global_space else param_key
        try:
            config_params = rospy.get_param(param_key)
        except OSError:
            sys.stderr.write('Warning: no ROS master running\n')
        except KeyError:
            rospy.loginfo(f'Config params not initialized from {param_key}')
        else:
            self._update_property_map_recursively(
                property_map, config_params, update_base
            )
        if add_cb:
            property_map.valueChanged.connect(
                functools.partial(self._on_value_changed, param_key)
            )
            if not hasattr(self, '_base_map'):
                self._base_map = dict()
            self._base_map[param_key] = property_map

        return property_map

    @staticmethod
    def _to_camel_case(snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    @staticmethod
    def _to_snake_case(camel_str):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()

    def _update_property_map_recursively(
        self, property_map, params, update_base=None
    ):
        if not hasattr(self, '_key_map'):
            self._key_map = dict()  # maps camel case keys to snake case keys
        for key in params:
            camel_key = Config._to_camel_case(key)
            new_base = f'{update_base}/{key}' if update_base else None

            if isinstance(params[key], dict):
                new_map = QQmlPropertyMap(property_map)
                property_map.insert(camel_key, new_map)
                if new_base:
                    new_map.valueChanged.connect(
                        functools.partial(self._on_value_changed, new_base)
                    )
                self._update_property_map_recursively(
                    new_map, params[key], new_base
                )

            else:
                property_map.insert(camel_key, params[key])
                if new_base:
                    self._key_map[f'{update_base}/{camel_key}'] = new_base

    def _on_update_received(self, key, value):
        key_parts = key.split('/')
        if len(key_parts) == 0:
            return

        property_map = self._base_map.get(key_parts[0], None)
        if property_map is None:
            return

        for key_ in key_parts[1:-1]:
            camel_key = self._to_camel_case(key_)
            property_map = property_map.value(camel_key)
            if property_map is None:
                return
        camel_key = self._to_camel_case(key_parts[-1])

        current_value = property_map.value(camel_key)
        if value != current_value:
            property_map.insert(camel_key, value)

    def _on_value_changed(self, base, key, value):
        camel_key = f'{base}/{key}'
        snake_key = self._key_map.get(camel_key, None)
        if not snake_key:
            snake_key = Config._to_snake_case(camel_key)
            self._key_map[camel_key] = snake_key
        if isinstance(value, QJSValue):
            value = value.toVariant()
        self._config.set_param(snake_key, value)

    @Slot()
    def _shutdown(self):
        self._config.stop()

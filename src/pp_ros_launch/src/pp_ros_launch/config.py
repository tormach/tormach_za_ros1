import os
import yaml
import logging

_stash = {}  # Singleton storage


class PPROSContainerConfig:
    """A class for PathPilot ROS launcher configuration stored in a YAML
    file, and defaults

    From the launcher UI inside the container, this class is used to
    generate and write a configuration file to tell the Docker container
    launcher what to do on the next launch.

    From the manager process (on the host OS) that launches the ROS
    container, this class is used to read the configuration file or to
    generate reasonable defaults in its absence.
    """

    _default_state_path = None
    name = 'config'

    # Change to @classmethod @property in Python >= 3.9
    @classmethod
    def default_state_path(cls) -> str:
        if PPROSContainerConfig._default_state_path is None:
            try:
                PPROSContainerConfig._default_state_path = (
                    f'{os.environ["HOME"]}/.pathpilot/launcher_config.yaml'
                )
            except (ValueError, KeyError):
                cls.cls_logger().critical(
                    "No environment variable $HOME. Setting temporary volatile launcher_config file!"
                )
                PPROSContainerConfig._default_state_path = (
                    '/tmp/launcher_config.yaml'
                )
        return PPROSContainerConfig._default_state_path

    @property
    def log_name(self):
        return self.name

    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.log_name)
        return self._logger

    @classmethod
    def cls_logger(cls):
        return logging.getLogger(cls.name)

    @classmethod
    def init_logging(cls, level="INFO"):
        level_int = getattr(logging, level)
        logging.basicConfig(level=level_int)

    @classmethod
    def set_stash(cls, var, val):
        _stash[var] = val
        return val

    @classmethod
    def get_stash(cls, var=None):
        if var is None:
            return _stash
        else:
            return _stash.get(var, None)

    @classmethod
    def clear_stash(cls):
        for k in list(_stash.keys()):
            _stash.pop(k)

    @classmethod
    def set_state_path(cls, path):
        cls.set_stash('state_path', path)

    @classmethod
    def get_state_path(cls):
        return cls.get_stash('state_path')

    def __init__(self, state_path=None):
        if state_path is not None:
            self.set_state_path(state_path)
        # Make sure the state_path is never set to null
        elif self.get_state_path() is None:
            self.set_state_path(self.default_state_path())

    @classmethod
    def add_cl_state_file_arg(cls, parser):
        path = cls.default_state_path()
        parser.add_argument(
            '--state-file',
            help='State file for storing configuration (default %s)' % path,
            type=str,
            default=path,
        )

    # -------------
    # Read/write config from/to file

    @classmethod
    def read_config(cls):
        config = cls._clear_config()  # Start fresh
        path = cls.get_state_path()
        if os.path.exists(path):
            with open(path) as f:
                data = yaml.safe_load(f)
                if data:
                    config.update(data)
        return config

    @classmethod
    def write_config(cls):
        config = cls.get_stash('config')
        path = cls.get_state_path()
        if not config:
            raise RuntimeError('Configuration not yet set')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False)
        except OSError as e:
            cls.cls_logger().warning(
                f'Unable to write state file {path}:  {str(e)}'
            )

    # -------------
    # Config initialization

    @classmethod
    def _clear_config(cls):
        if cls.get_stash('config') is None:
            cls.set_stash('config', dict())
        config = cls.get_stash('config')
        for k in list(config.keys()):
            config.pop(k)
        return config

    @classmethod
    def init_config(cls, cl_args=None, state_file=None):
        cls.set_stash('cl_args', cl_args)
        if cl_args is None:
            cls.set_state_path(state_file or cls.default_state_path())
        else:
            cls.set_state_path(cl_args.state_file)
        cls.read_config()

    # -------------
    # Config attributes

    @classmethod
    def _get_config_obj(cls):
        config = cls.get_stash('config')
        if config is None:
            return cls._clear_config()
        else:
            return config

    @property
    def config(self):
        return self._get_config_obj()

    @classmethod
    def get_config(cls, item, default=None):
        return cls._get_config_obj().get(item, default)

    @classmethod
    def set_config(cls, item: str, value) -> None:
        if not isinstance(item, str):
            cls.cls_logger().critical(f'Key "{item}" is not string!')
            raise KeyError(f'{item} must be a string!')
        cls.cls_logger().info(f'Setting config "{item}" = "{value}"')
        cls._get_config_obj()[item] = value

    @classmethod
    def remove_config_key(cls, key: str) -> None:
        try:
            cls.cls_logger().info(f'Removing key "{key}"" from config')
            del cls._get_config_obj()[key]
        except KeyError:
            cls.cls_logger().warning(
                f'Could not remove key "{key}"" from config'
            )

    # -------------
    # Command line args

    @property
    def cl_args(self):
        return self.get_stash('cl_args')

    @classmethod
    def get_cl_arg(cls, key, default=None):
        cl_args = cls.get_stash('cl_args')
        if not cl_args:
            return default
        else:
            return cl_args.__dict__.get(key, default)

    # -------------
    # Command line or config

    def get_cl_or_config(self, item, default=None, return_source=False):
        # Command line gets priority
        res = self.get_cl_arg(item, None)
        src = 'command line'
        if res is None:
            # State file next
            res = self.get_config(item, None)
            src = 'state file'
        if res is None:
            # Default last
            res = default
            src = 'default'
        if return_source:
            return res, src
        else:
            return res

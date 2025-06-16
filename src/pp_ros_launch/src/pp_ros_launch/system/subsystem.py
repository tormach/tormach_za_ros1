import os
import grp
import distutils.spawn
import subprocess
from pp_ros_launch.config import PPROSContainerConfig
from collections import namedtuple
from typing import Dict

_cache = {}


class SubSystemCheck(PPROSContainerConfig):
    """Base class for all subsystem checks."""

    name = None  # Override in subclasses
    fatal = True
    depends = None
    depends_nonfatal = None

    @property
    def log_name(self):
        return 'check_%s' % self.name

    # ----------------------------------
    # Helpers
    #
    def have_executable(self, name):
        return distutils.spawn.find_executable(name) is not None

    def path_exists(self, path):
        return os.path.exists(path)

    def get_cmd_stdout(self, args):
        try:
            data = subprocess.check_output(args)
        except subprocess.CalledProcessError:
            return None
        return data

    def read_file_contents(self, path, first_line_only=False):
        if not self.path_exists(path):
            return None
        if first_line_only:
            with open(path) as f:
                return f.readline().rstrip()
        else:
            return open(path)

    def docker_volume_param(self, src_path, dst_path=None, mode='rw'):
        if dst_path is None:
            dst_path = src_path
        return {src_path: {'bind': dst_path, 'mode': mode}}

    def docker_mount_param(
        self,
        target,
        source,
        type: str = 'bind',
        read_only=False,
        propagation='shared',
    ) -> Dict:
        if type not in ['bind', 'volume', 'tmpfs', 'npipe']:
            raise RuntimeError(
                f'The type {type} for mount from {source} '
                f'to {target} is not a valid one!'
            )
        if propagation not in [
            'private',
            'shared',
            'slave',
            'rprivate',
            'rshared',
            'rslave',
        ]:
            raise RuntimeError(
                f'The propagation {propagation} for mount from {source} '
                f'to {target} is not a valid one!'
            )

        item = {
            'Target': target,
            'Source': source,
            'Type': type,
            'ReadOnly': read_only,
            'BindOptions': {'Propagation': propagation},
        }

        return item

    def docker_environ_param(self, var_name, var_value=None):
        if var_value is None:
            var_value = os.environ.get(var_name, '')
        return {var_name: var_value}

    def check_user_in_group(self, group_name):
        try:
            grnam = grp.getgrnam(group_name)
        except KeyError:
            # Group doesn't exist
            return False
        return grnam.gr_gid in os.getgroups()

    # ----------------------------------
    # Cache
    #

    @classmethod
    def have_cache(cls, attr=None, name=None):
        if (name or cls.name) not in _cache:
            return False
        if attr is None:
            return True  # Check only that test was run
        return attr in _cache[name or cls.name]

    @classmethod
    def get_cache(cls, attr=None, name=None, all=False):
        if all:
            return _cache
        if attr is None:
            # Return whole cache
            return _cache.get(name or cls.name, dict())
        else:
            return _cache[name or cls.name][attr]

    @classmethod
    def set_cache(cls, attr, val, name=None):
        _cache.setdefault(name or cls.name, dict())[attr] = val
        return val

    @classmethod
    def clear_cache(cls, name=None):
        '''Force check to run again'''
        _cache.pop(name or cls.name, None)

    # ----------------------------------
    # Config
    #

    @classmethod
    def add_cl_args(cls, parser):
        # For subclasses to implement
        return

    # ----------------------------------
    # Methods to override in subclasses
    #
    def run_check(self):
        raise NotImplementedError("run_check() must be implemented in subclass")

    def docker_run_volumes(self):
        return dict()

    def docker_run_mounts(self):
        return list()

    def docker_run_environment(self):
        return dict()

    def docker_run_args(self):
        return dict()

    def result_data(self) -> dict:
        return dict()

    # ----------------------------------
    # Check result messages
    #

    CheckLog = namedtuple('CheckLog', ['level', 'msg'])
    CheckLog.msg_level_info = 1
    CheckLog.msg_level_warning = 2
    CheckLog.msg_level_fatal = 3
    CheckLog.msg_level_recommendation = 4

    @property
    def logs(self):
        if not self.have_cache('logs'):
            self.set_cache('logs', list())
        return self.get_cache('logs')

    def log_message(self, level, msgs, logger=None):
        if isinstance(msgs, str):
            msgs = [msgs]
        self.logs.extend([self.CheckLog(level, msg) for msg in msgs])
        if logger is not None:
            for msg in msgs:
                logger(msg)

    def log_info(self, msgs):
        self.log_message(self.CheckLog.msg_level_info, msgs, self.logger.info)

    def log_warning(self, msgs):
        self.log_message(
            self.CheckLog.msg_level_warning, msgs, self.logger.warning
        )

    def log_fatal(self, msgs):
        if self.is_fatal():
            self.log_message(
                self.CheckLog.msg_level_fatal, msgs, self.logger.fatal
            )
        else:
            self.log_message(
                self.CheckLog.msg_level_warning, msgs, self.logger.warning
            )

    def log_recommendation(self, msgs):
        self.log_message(self.CheckLog.msg_level_recommendation, msgs)

    # ----------------------------------
    # Internal logic
    #

    def prereq_failed(self):
        if self.depends is None:
            return False
        # Dependencies should already have run
        if not self.have_cache(name=self.depends):
            err = "Check {} depends on unexecuted {}".format(
                self.name, self.depends
            )
            self.log_fatal(err)
            raise RuntimeError(err)
        return not self.get_cache('result', name=self.depends)

    def is_fatal(self):
        if self.have_cache('fatal', name=self.depends):
            return self.fatal and self.get_cache('fatal', name=self.depends)
        else:
            return self.fatal

    def _run_check(self):
        if self.have_cache('result'):
            # Check already ran; return cached result
            return self.get_cache('result')
        elif self.prereq_failed():
            # If any dependency has failed, this one fails, too, without running
            self.log_info(
                "Dependency %s failed; skipping (%s)"
                % (self.depends, 'fatal' if self.is_fatal() else 'nonfatal')
            )
            res = False
        else:
            # Run the check and cache the result
            res = self.set_cache('result', self.run_check())
        self.set_cache('fatal', self.is_fatal())
        self.set_cache('result', res)
        return res

    # ----------------------------------
    # Methods for external use
    #

    @property
    def check_result(self):
        return self._run_check()

    @property
    def check_result_nonfatal(self):
        return self.check_result or not self.is_fatal()

    def cached_result(self):
        if not self.have_cache('result'):
            err = "Requested result without first executing check"
            self.log_fatal(err)
            raise RuntimeError(err)
        return self.get_cache('result')


class SubSystemGroupCheck(SubSystemCheck):
    """Base class for checking POSIX groups."""

    group = None  # Subclasses must override

    @property
    def my_groups(self):
        """Return list of POSIX group IDs the user belongs to"""
        return os.getgroups()

    @property
    def group_gid(self):
        """Translate group name to ID"""
        try:
            grnam = grp.getgrnam(self.group)
        except KeyError:
            return None
        return grnam.gr_gid

    def run_check(self):
        if self.group_gid in self.my_groups:
            self.log_info(f"User found in '{self.group}' group")
            return True
        else:
            self.log_fatal(f"User not in '{self.group}' group")
            self.log_recommendation(
                f"Add user to '{self.group}' group and reboot"
            )
            return False


class SubSystemDockerEnvCheck(SubSystemCheck):
    """Base class for passing environment variables into the Docker
    container.
    """

    env_vars = None  # Subclasses must override
    fatal = False  # If True, fail if environment variable(s) absent

    @property
    def _canon_env_vars(self):
        if isinstance(self.env_vars, str):
            return [self.env_vars]
        else:
            return self.env_vars

    def run_check(self):
        vars_set = self.set_cache('vars_set', dict())
        vars_unset = self.set_cache('vars_unset', list())
        for var in self._canon_env_vars:
            if var in os.environ:
                val = os.environ[var]
                vars_set[var] = val
                self.log_info(f'Setting env var {var} = "{val}"')
            else:
                vars_unset.append(var)

        if len(vars_unset) == 0:
            return True
        unset_vars = ', '.join(self.get_cache('vars_unset'))
        self.log_fatal(f"Environment variables {unset_vars} absent")
        return False

    def docker_run_environment(self):
        return self.get_cache('vars_set') if self.cached_result() else dict()


class SubSystemDockerVolumeCheck(SubSystemCheck):
    """Base class for bind-mounting volumes into the Docker container."""

    path = None  # Subclasses must override
    fatal = False  # If True, fail and don't mount if path doesn't exist
    absent_ok = False  # If True, mount even if path doesn't exist

    @property
    def host_path(self):
        # May be overridden to specify different host-path or volume-name
        return self.path

    def run_check(self):
        if not self.host_path.startswith('/'):
            # Docker named volume
            self.log_info(
                f"Creating named volume {self.host_path} at {self.path}"
            )
            return True

        exists = os.path.exists(self.host_path)
        self.set_cache('path_exists', exists)

        if exists:  # Success
            self.log_info(f"Bind-mounting {self.host_path}")
            return True

        if self.absent_ok:  # Success, though path doesn't exist
            self.log_info('Bind-mounting absent path %s' % self.host_path)
            return True

        # Failure
        self.log_fatal("Unable to bind-mount absent path %s" % self.host_path)
        return False

    def docker_run_volumes(self):
        if self.cached_result():
            return self.docker_volume_param(self.host_path, self.path)
        else:
            return dict()


class SubSystemDockerMountCheck(SubSystemCheck):
    """Base class for creating mounts into the Docker container."""

    source = None  # Subclasses must override, pathlib.Path type
    target = None  # Subclasses must override, pathlib.Path type
    mount = 'bind'  # Subclass may override
    propagation = 'shared'  # Subclass may override
    fatal = False  # If True, fail and don't mount if path doesn't exist
    absent_ok = False  # If True, mount even if path doesn't exist

    @property
    def host_path(self):
        # May be overridden to specify different host-path
        return self.source

    @property
    def container_path(self):
        # May be overridden to specify different container-path
        return self.target

    @property
    def mount_type(self):
        # May be overridden to specify different mount types
        return self.mount

    @property
    def mount_propagation(self):
        # May be overridden to specify different mount propagation scheme
        return self.propagation

    def run_check(self):
        # Interested in mounting from the host to container only
        exists = os.path.exists(self.host_path)
        self.set_cache('path_exists', exists)

        if exists:  # Success
            self.log_info(
                f"Creating mount from {self.host_path} to {self.container_path}"
            )
            return True

        if self.absent_ok:  # Success, though path doesn't exist
            self.log_info(
                f'Creating mount from absent {self.host_path} to {self.container_path}'
            )
            return True

        # Failure
        self.log_fatal(
            f'Unable to create mount from {self.host_path} to {self.container_path}'
        )
        return False

    def docker_run_mounts(self):
        if self.cached_result():
            return [
                self.docker_mount_param(
                    target=self.container_path,
                    source=self.host_path,
                    type=self.mount_type,
                    propagation=self.mount_propagation,
                )
            ]
        else:
            return []


class SubSystemExecutableCheck(SubSystemCheck):
    """Base class for asserting the existence of an executable in ``$PATH``."""

    executable = None  # Subclasses must override

    def run_check(self):
        if distutils.spawn.find_executable(self.executable) is None:
            self.log_fatal("Unable to find executable %s" % self.executable)
            return False
        else:
            self.log_info("Found executable %s" % self.executable)
            return True


class SubSystem(PPROSContainerConfig):
    """Base class for a subsystem with one or more associated checks."""

    name = None  # Override in subclasses

    check_classes = list()

    def __init__(self):
        super().__init__()
        self.checks = [c() for c in self.check_classes]

    @classmethod
    def clear_cache(cls):
        for c in cls.check_classes:
            c.clear_cache()

    @classmethod
    def get_cache(cls):
        return _cache

    @classmethod
    def add_cl_args(cls, parser):
        for c in cls.check_classes:
            c.add_cl_args(parser)

    @property
    def check_results(self):
        return all([c.check_result for c in self.checks])

    @property
    def check_results_nonfatal(self):
        return all([c.check_result_nonfatal for c in self.checks])

    def result_data(self) -> dict:
        data: dict = dict()
        for c in self.checks:
            data.update(c.result_data())
        return data

    def failed_fatal_checks(self) -> list:
        _failed_checks: list = list()
        for s in self.checks:
            if not s.check_result and s.is_fatal():
                _failed_checks.append(s.name)
        return _failed_checks

    def cached_result(self):
        return all(c.cached_result() for c in self.checks)

    def docker_run_environment(self):
        env = {}
        for c in self.checks:
            env.update(c.docker_run_environment())
        return env

    def docker_run_volumes(self):
        vol = {}
        [vol.update(c.docker_run_volumes()) for c in self.checks]
        return vol

    def docker_run_mounts(self):
        mounts = []
        [mounts.extend(c.docker_run_mounts()) for c in self.checks]
        return mounts

    def docker_run_args(self):
        args = {}
        [args.update(c.docker_run_args()) for c in self.checks]
        for key, val in (
            ('environment', self.docker_run_environment()),
            ('volumes', self.docker_run_volumes()),
        ):
            if val:
                args.update({key: val})
        return args

    SubSystemCheckLog = namedtuple(
        'SubSystemCheckLog', ['check', 'level', 'msg']
    )
    for a in dir(SubSystemCheck.CheckLog):
        if not a.startswith('msg_level_'):
            continue
        setattr(SubSystemCheckLog, a, getattr(SubSystemCheck.CheckLog, a))

    @property
    def logs(self, fail_only=False):
        logs = []
        for c in self.checks:
            if fail_only and c.cached_result():
                continue
            for log in c.logs:
                logs.append(self.SubSystemCheckLog(c.name, log.level, log.msg))
        return logs

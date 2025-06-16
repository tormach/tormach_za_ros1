import pytest
from unittest.mock import patch
from pp_ros_launch.system.subsystem import (
    SubSystemCheck,
    SubSystemGroupCheck,
    SubSystemDockerEnvCheck,
    SubSystemDockerVolumeCheck,
    SubSystemDockerMountCheck,
    SubSystemExecutableCheck,
    SubSystem,
)
from pprint import pformat


class TestSubSystemCheck:
    class SubSystemCheckTestClass(SubSystemCheck):
        name = "test_check"
        will_pass = True

        def run_check(self):
            if self.will_pass:
                self.log_info('bogus')
            else:
                self.log_warning('bogus')
            return self.will_pass

    test_class = SubSystemCheckTestClass
    fatal = True
    always_passes = False
    expected_volumes = None
    expected_mounts = None
    skip_env_check = False

    def obj_fixture_hook(self):
        # Q&D way to patch extra fixture work into all object
        # fixtures, pass or fail
        pass

    def obj_fixture(
        self, clear_stash=True, clear_cache=True, stop_patches=True
    ):
        try:
            obj = self.test_class()
            self.obj_fixture_hook()
            yield obj
            try:
                print('cache:', pformat(obj.get_cache()))
                print('info:', pformat(obj.info))
                print('warning:', obj.warning)
            except Exception:
                pass
        except Exception:
            raise
        finally:
            if clear_stash:
                self.clear_stash()
            if clear_cache:
                self.clear_cache()
            if stop_patches:
                self.patch_stopall()

    def patch_stopall(self):
        print("Stopping patches")
        patch.stopall()

    def clear_cache(self):
        print("Clearing cache")
        cache = self.test_class.get_cache(all=True)
        for k in list(cache.keys()):
            cache.pop(k)

    def clear_stash(self):
        print("Clearing stash")
        self.test_class.clear_stash()

    @pytest.fixture
    def obj(self):
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_pass(self):
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self):
        for obj in self.obj_fixture():
            if hasattr(obj, 'will_pass'):
                obj.will_pass = False
            yield obj

    def test_attrs(self):
        assert self.test_class.name is not None
        for attr_name in ["depends", "depends_nonfatal"]:
            attr = getattr(self.test_class, attr_name)
            print("attr_name:", attr_name, "  value:", attr)
            assert (
                attr is None
                or isinstance(attr, str)
                or isinstance(attr, property)
            )
        assert self.always_passes or (self.test_class.fatal is self.fatal)

    # ----------------------------------
    # Helpers
    #
    def test_have_executable_true(self, obj, mock_find_executable):
        self.executable_map = dict(bogus='/test/bogus')
        res = obj.have_executable('bogus')
        print(mock_find_executable.mock_calls)
        mock_find_executable.assert_called_with('bogus')
        assert res is True

    def test_have_executable_false(self, obj, mock_find_executable):
        self.executable_map = dict()
        res = obj.have_executable('bogus')
        print(mock_find_executable.mock_calls)
        mock_find_executable.assert_called_with('bogus')
        assert res is False

    def test_path_exists_true(self, obj, mock_open):
        self.file_data = {'/test/bogus': ''}
        res = obj.path_exists('/test/bogus')
        print(self.mock_os_path_exists.mock_calls)
        self.mock_os_path_exists.assert_called_with('/test/bogus')
        assert res is True

    def test_path_exists_false(self, obj, mock_open):
        self.file_data = dict()
        res = obj.path_exists('/test/bogus')
        print(self.mock_os_path_exists.mock_calls)
        self.mock_os_path_exists.assert_called_with('/test/bogus')
        assert res is False

    def test_get_cmd_stdout_success(self, obj, mock_subprocess_popen):
        args = ['bogus_cmd', 'arg1']
        res = obj.get_cmd_stdout(args)
        print(self.mock_popen.mock_calls)
        self.mock_check_output.assert_called_with(args)
        assert res is self.mock_subprocess_stdout

    def test_get_cmd_stdout_fail(self, obj, mock_subprocess_popen):
        args = ['bogus_cmd', 'arg1']
        mock_subprocess_popen.wait.return_value = 1  # Fail
        res = obj.get_cmd_stdout(args)
        print(self.mock_check_output.mock_calls)
        self.mock_check_output.assert_called_with(args)
        assert res is self.mock_subprocess_stdout

    def test_read_file_contents_fail(self, obj, mock_open):
        self.file_data = dict()
        res = obj.read_file_contents('/nonexistent/file')
        print(self.mock_os_path_exists.mock_calls)
        self.mock_os_path_exists.assert_called_with('/nonexistent/file')
        assert res is None

    def test_read_file_contents_all(self, obj, mock_open):
        self.file_data = {'/some/file': 'foo\nbar\nbaz\n'}
        print(self.file_data)
        with obj.read_file_contents('/some/file') as res:
            print(
                "os.path.exists() calls:", self.mock_os_path_exists.mock_calls
            )
            self.mock_os_path_exists.assert_called_with('/some/file')
            print("open() calls:", self.mock_open.mock_calls)
            self.mock_open.assert_called_with('/some/file')
            lines = [line for line in res]
            assert len(lines) == 3

    def test_read_file_contents_first_line(self, obj, mock_open):
        self.file_data = {'/some/file': 'foo\n'}
        res = obj.read_file_contents('/some/file', first_line_only=True)
        print("os.path.exists() calls:", self.mock_os_path_exists.mock_calls)
        self.mock_os_path_exists.assert_called_with('/some/file')
        print("open() calls:", self.mock_open.mock_calls)
        self.mock_open.assert_called_with('/some/file')
        print("result:", res)
        print(self.mock_open.mock_calls)
        assert res == "foo"

    def check_user_in_group(self, obj, mock_groups):
        self.sys_groups = dict(docker=801, ethercat=802, restricted_group=88)
        self.group_ids = [17, 801, 802]  # NOT in 88

        # Check for user in existing group
        assert obj.check_user_in_group('docker')

        # Check user NOT in existing group
        assert not obj.check_user_in_group('restricted_group')

        # Check user not in absent group
        assert not obj.check_user_in_group('absent_group')

    # ----------------------------------
    # Cache
    #
    def test_cache(self, obj):
        # No cache at beginning
        print('Depends:', self.test_class.depends)
        print('Beginning cache:', pformat(self.test_class.get_cache(all=True)))
        depends = 1 if self.test_class.depends else 0
        assert len(obj.get_cache(all=True)) == depends
        obj.clear_cache()
        assert len(obj.get_cache(all=True)) == depends

        # Set, get, have
        assert obj.have_cache() is False
        assert obj.set_cache('test_attr', 'test_val') == 'test_val'
        assert len(obj.get_cache(all=True)) == 1 + depends
        assert obj.name in obj.get_cache(all=True)
        assert len(obj.get_cache(all=True)[obj.name]) == 1
        assert obj.have_cache() is True
        assert obj.get_cache('test_attr') == 'test_val'

        # Set, get on another check
        assert obj.have_cache(name='check2') is False
        assert (
            obj.set_cache('test_attr', 'test_val2', name='check2')
            == 'test_val2'
        )
        assert len(obj.get_cache(all=True)) == 2 + depends
        assert 'check2' in obj.get_cache(all=True)
        assert len(obj.get_cache(all=True)['check2']) == 1
        assert obj.have_cache(name='check2') is True
        assert obj.get_cache('test_attr', name='check2') == 'test_val2'
        assert obj.get_cache('test_attr') == 'test_val'  # Sanity

        # Clear
        assert len(obj.get_cache(all=True)) == 2 + depends
        assert obj.have_cache() is True
        assert obj.have_cache(name='check2') is True
        obj.clear_cache()
        assert len(obj.get_cache(all=True)) == 1 + depends
        assert obj.have_cache() is False
        assert obj.have_cache(name='check2') is True
        obj.clear_cache(name='check2')
        assert len(obj.get_cache(all=True)) == 0 + depends
        assert obj.have_cache() is False
        assert obj.have_cache(name='check2') is False

    # ----------------------------------
    # Methods to override in subclasses
    #

    def test_run_check_pass(self, obj_pass):
        print(obj_pass)
        assert obj_pass.check_result is True

    def test_run_check_fail(self, obj_fail):
        if self.always_passes:
            return
        print(obj_fail)
        assert obj_fail.check_result is False

    def test_docker_run_volumes_pass(self, obj_pass):
        assert obj_pass.check_result is True
        drv = obj_pass.docker_run_volumes()
        assert isinstance(drv, dict)
        if self.expected_volumes is None:
            return
        assert len(drv) == len(self.expected_volumes)
        for key in self.expected_volumes:
            assert key in drv
            if self.expected_volumes[key] is not None:
                assert self.expected_volumes[key] == drv[key]

    def test_docker_run_volumes_fail(self, obj_fail):
        if self.always_passes:
            return
        assert obj_fail.check_result is False
        drv = obj_fail.docker_run_volumes()
        assert isinstance(drv, dict)
        assert len(drv) == 0

    def test_docker_run_environment_pass(self, obj_pass):
        assert obj_pass.check_result is True
        dre = obj_pass.docker_run_environment()
        assert isinstance(dre, dict)
        expected = getattr(self, 'expected_environment', None)
        if expected is None:
            return
        expected = expected.copy()
        expected.pop('PATH', None)
        assert len(dre) == len(expected)
        for key in expected:
            assert key in dre
            if expected[key] is not None:
                assert expected[key] == dre[key]

    def test_docker_run_environment_fail(self, obj_fail):
        if self.always_passes or self.skip_env_check:
            return
        assert obj_fail.check_result is False
        dre = obj_fail.docker_run_environment()
        assert isinstance(dre, dict)
        assert len(dre) == 0

    def test_docker_run_args(self, obj_pass):
        assert obj_pass.check_result  # Run check
        assert isinstance(obj_pass.docker_run_args(), dict)

    # ----------------------------------
    # Check result messages
    #

    def test_log_functions(self, obj_pass):
        assert len(obj_pass.logs) == 0
        obj_pass.log_info('info log 1')
        obj_pass.log_info(['info log 2', 'info log 3'])
        obj_pass.log_warning('warning log 1')
        obj_pass.log_fatal(['fatal log 1'])
        obj_pass.log_recommendation('recommendation log 1')

        print(obj_pass.logs)
        assert len(obj_pass.logs) == 6
        assert obj_pass.logs == [
            (obj_pass.CheckLog.msg_level_info, 'info log 1'),
            (obj_pass.CheckLog.msg_level_info, 'info log 2'),
            (obj_pass.CheckLog.msg_level_info, 'info log 3'),
            (obj_pass.CheckLog.msg_level_warning, 'warning log 1'),
            (
                (
                    obj_pass.CheckLog.msg_level_fatal
                    if self.fatal
                    else obj_pass.CheckLog.msg_level_warning
                ),
                'fatal log 1',
            ),
            (
                obj_pass.CheckLog.msg_level_recommendation,
                'recommendation log 1',
            ),
        ]

    def test_logs_pass(self, obj_pass):
        assert len(obj_pass.logs) == 0
        assert obj_pass.check_result is True
        print(obj_pass.logs)
        assert len(obj_pass.logs) > 0
        # All logs must be info messages
        for log in obj_pass.logs:
            assert log.level == obj_pass.CheckLog.msg_level_info

    def test_logs_fail(self, obj_fail):
        if self.always_passes:
            # Implement only for checks that aren't always True
            return
        assert len(obj_fail.logs) == 0
        assert obj_fail.check_result is False
        print(obj_fail.logs)
        assert len(obj_fail.logs) > 0
        # Must be at least one error message
        warnings, fatals, recommendations = (0, 0, 0)
        for log in obj_fail.logs:
            if log.level == obj_fail.CheckLog.msg_level_warning:
                warnings += 1
            if log.level == obj_fail.CheckLog.msg_level_fatal:
                fatals += 1
            if log.level == obj_fail.CheckLog.msg_level_recommendation:
                recommendations += 1
        assert fatals + warnings > 0

    # ----------------------------------
    # Methods for external use
    #

    def test_check_result_pass(self, obj_pass):
        assert obj_pass.check_result is True

    def test_check_result_fail(self, obj_fail):
        if self.always_passes:
            return
        assert obj_fail.check_result is False

    def test_check_result_nonfatal_pass(self, obj_pass):
        assert obj_pass.check_result_nonfatal is True

    def test_check_result_nonfatal_fail(self, obj_fail):
        if self.always_passes:
            return
        if self.fatal:
            assert obj_fail.check_result_nonfatal is False
        else:
            assert obj_fail.check_result_nonfatal is True


class TestSubSystemGroupCheck(TestSubSystemCheck):
    class SubSystemGroupCheckTestClass(SubSystemGroupCheck):
        name = "test_group_check"
        group = 'test_group'

    test_class = SubSystemGroupCheckTestClass
    sys_groups = dict(test_group=42)
    group_ids = sorted([17] + list(sys_groups.values()))

    @pytest.fixture()
    def obj_pass(self, mock_groups):
        print('sys_groups:', self.sys_groups)
        print('group_ids:', self.group_ids)
        print('expected group:', self.test_class.group)
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_groups):
        # Fail because user not in group
        self.group_ids = []
        print('sys_groups:', self.sys_groups)
        print('group_ids:', self.group_ids)
        print('expected group:', self.test_class.group)
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail_nosysgroup(self, mock_groups):
        # Fail because group not on system
        self.sys_groups = {}
        print('sys_groups:', self.sys_groups)
        print('group_ids:', self.group_ids)
        print('expected group:', self.test_class.group)
        yield from self.obj_fixture()

    def test_attrs(self):
        super().test_attrs()
        assert self.test_class.group is not None

    def test_run_check_fail_nosysgroup(self, obj_fail_nosysgroup):
        assert obj_fail_nosysgroup.run_check() is False


class TestSubSystemDockerEnvCheck(TestSubSystemCheck):
    fatal = False
    expected_environment = dict(
        TEST_VAR1='TEST_VAR1_test', TEST_VAR2='TEST_VAR2_test'
    )

    class SubSystemDockerEnvCheckTestClass(SubSystemDockerEnvCheck):
        name = "test_docker_env_check"
        env_vars = ['TEST_VAR1', 'TEST_VAR2']

    test_class = SubSystemDockerEnvCheckTestClass

    @pytest.fixture
    def obj_pass(self, mock_env):
        for v in self.test_class.env_vars:
            self.env[v] = self.expected_environment[v]
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_fail(self, mock_env):
        for v in self.test_class.env_vars:
            self.env.pop(v, None)
        yield from self.obj_fixture()

    def test_attrs(self):
        super().test_attrs()
        assert isinstance(self.test_class.env_vars, list)
        assert len(self.test_class.env_vars) > 0


class TestSubSystemDockerVolumeCheck(TestSubSystemCheck):
    fatal = False

    class SubSystemDockerVolumeCheckTestClass(SubSystemDockerVolumeCheck):
        name = "test_docker_volume_check"
        path = "/tmp/test"

    test_class = SubSystemDockerVolumeCheckTestClass

    @pytest.fixture()
    def obj_pass(self, mock_open):
        self.file_data = {self.test_class.path: ''}
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_open):
        self.file_data = {self.test_class.path: None}
        yield from self.obj_fixture()

    @property
    def expected_volumes(self):
        path = self.test_class.path
        return {path: dict(bind=path, mode='rw')}

    def test_attrs(self):
        super().test_attrs()
        if isinstance(self.test_class.path, property):
            return  # Following checks don't make sense
        assert isinstance(self.test_class.path, str)
        assert self.test_class.path.startswith('/')


class TestSubSystemDockerMountCheck(TestSubSystemCheck):
    fatal = False

    class SubSystemDockerMountCheckTestClass(SubSystemDockerMountCheck):
        name = "test_docker_mount_check"
        source = "/tmp/test"
        target = "/tmp/test"

    test_class = SubSystemDockerMountCheckTestClass

    @pytest.fixture()
    def obj_pass(self, mock_open):
        self.file_data = {self.test_class.source: ''}
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_open):
        self.file_data = {self.test_class.source: None}
        yield from self.obj_fixture()

    @property
    def expected_mounts(self):
        return {
            'Target': self.test_class.target,
            'Source': self.test_class.source,
            'Type': 'bind',
            'ReadOnly': False,
            'BindOptions': {'Propagation': 'shared'},
        }

    def test_attrs(self):
        super().test_attrs()
        if isinstance(self.test_class.host_path, property):
            return  # Following checks don't make sense
        assert isinstance(self.test_class.host_path, str)
        assert self.test_class.host_path.startswith('/')


class TestSubSystemExecutableCheck(TestSubSystemCheck):
    fatal = True

    class SubSystemExecutableCheckTestClass(SubSystemExecutableCheck):
        name = "test_docker_volume_check"
        executable = "test_executable"

    test_class = SubSystemExecutableCheckTestClass

    @pytest.fixture()
    def obj_pass(self, mock_find_executable):
        self.executable_map[self.test_class.executable] = (
            "/usr/bin/" + self.test_class.executable
        )
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_find_executable):
        self.executable_map.pop(self.test_class.executable, None)
        yield from self.obj_fixture()

    def test_attrs(self):
        super().test_attrs()
        assert isinstance(self.test_class.executable, str)


class TestSubSystem:
    class SubSystemTestClass(SubSystem):
        name = "test_subsystem"
        check_classes = [TestSubSystemCheck.test_class]

        def set_will_pass(self, result):
            for c in self.checks:
                c.will_pass = result

    test_class = SubSystemTestClass

    check_test_classes = [TestSubSystemCheck]

    always_passes = False
    skip_env_check = False

    def obj_fixture_hook(self):
        # Q&D way to patch extra fixture work into all object
        # fixtures, pass or fail
        pass

    def obj_fixture(self, clear_cache=True, stop_patches=True):
        try:
            obj = self.test_class()
            self.obj_fixture_hook()
            yield obj
            try:
                print('cache:', pformat(obj.get_cache()))
                # print('info:', pformat(obj.info))
                # print('warning:', obj.warning)
            except Exception:
                pass
        except Exception:
            raise
        finally:
            if clear_cache:
                self.clear_cache()
            if stop_patches:
                self.patch_stopall()

    def clear_cache(self):
        print("Clearing cache")
        self.test_class.clear_cache()

    def patch_stopall(self):
        print("Stopping patches")
        patch.stopall()

    @pytest.fixture()
    def obj_pass(self):
        # check_fixtures = [c().get_obj_pass() for c in self.check_test_classes]
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self):
        # check_fixtures = [c().get_obj_fail() for c in self.check_test_classes]
        for obj in self.obj_fixture():
            if hasattr(obj, 'set_will_pass'):
                obj.set_will_pass(False)
            yield obj

    def test_attrs(self):
        assert self.test_class.name is not None
        assert len(self.test_class.check_classes) > 0
        for i in self.test_class.check_classes:
            assert issubclass(i, SubSystemCheck)

    def test_init(self, obj_pass):
        assert len(obj_pass.checks) == len(self.test_class.check_classes)
        for o, c in zip(obj_pass.checks, self.test_class.check_classes):
            assert isinstance(o, c)

    def test_check_results_pass(self, obj_pass):
        res = obj_pass.check_results
        for i in obj_pass.checks:
            print("check name:", i.name, "  result:", i.check_result)
            assert i.check_result
        assert res

    def test_check_results_fail(self, obj_fail):
        if self.always_passes:
            return
        res = obj_fail.check_results
        checks_have_deps = False
        for i in obj_fail.checks:
            if i.name in [j.depends for j in obj_fail.checks]:
                print("check name:", i.name, "  skipping dependency")
                checks_have_deps = True
                continue
            print("check name:", i.name, "  result:", i.check_result)
        if not checks_have_deps:
            assert not res

    def test_docker_run_environment_pass(self, obj_pass):
        assert obj_pass.check_results is True
        dre = obj_pass.docker_run_environment()
        for c in obj_pass.checks:
            for key, val in c.docker_run_environment().items():
                assert key in dre
                assert dre[key] == val

    def test_docker_run_environment_fail(self, obj_fail):
        if self.always_passes or self.skip_env_check:
            return
        assert obj_fail.check_results is False
        dre = obj_fail.docker_run_environment()
        assert len(dre) == 0

    def test_docker_run_volumes_pass(self, obj_pass):
        assert obj_pass.check_results is True
        drv = obj_pass.docker_run_volumes()
        for c in obj_pass.checks:
            for key, val in c.docker_run_volumes().items():
                assert key in drv
                assert drv[key] == val

    def test_docker_run_volumes_fail(self, obj_fail):
        if self.always_passes:
            return
        assert obj_fail.check_results is False
        print(obj_fail.docker_run_volumes())
        drv = obj_fail.docker_run_volumes()
        assert len(drv) == 0

    def test_docker_run_args_pass(self, obj_pass):
        assert obj_pass.check_results is True
        dra = obj_pass.docker_run_args()
        for c in obj_pass.checks:
            print(c)
            print(c.docker_run_args)
            for key, val in c.docker_run_args().items():
                assert key in dra
                assert dra[key] == val

    def test_docker_run_args_fail(self, obj_fail):
        if self.always_passes:
            return
        assert obj_fail.check_results is False
        dra = obj_fail.docker_run_args()
        assert len(dra) == 0

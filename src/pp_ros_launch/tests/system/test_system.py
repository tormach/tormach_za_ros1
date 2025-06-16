import pytest
from functools import reduce
from pp_ros_launch.system import SystemChecks
from pp_ros_launch.system.ethercat import EtherCAT
from pprint import pformat
import sys

if sys.version_info[0] == 2:

    def my_bytes(s, enc):
        return bytes(s)

else:

    def my_bytes(s, enc):
        return bytes(s, enc)


class TestSystemChecks:
    tc = SystemChecks
    # Temporarily add the EtherCAT class for tests only, the whole Ethercat is
    # disabled for non-ZA6 systems
    #
    # The funnier and cleaner way to solve this would be to create a deep copy
    # of the class object (not instance) and modify the recipe, the right way to
    # solve this would be to ensure the EtherCAT can be tested on non-ZA6
    # systems
    subsystem = {ssc.name: ssc for ssc in [*tc.subsystem_classes, EtherCAT]}
    subsystemcheck = {
        cc.name: cc
        for cc in reduce(
            lambda x, y: x + y, [ss.check_classes for ss in subsystem.values()]
        )
    }

    # Fixture:  uid, gid
    user = 'pathpilot'
    home = '/home/pathpilot'
    uid = 1000
    gid = 1000

    # Fixture:  files
    file_data = {
        # EthercatKmodLoaded
        '/proc/modules': (
            'foo\nbar\n'
            'ec_master 262144 1 ec_generic, Live 0xffffffffc0801000 (O)\n'
            'baz\n'
        ),
        # Workdir
        '/home/pathpilot': '',
        # MotherboardHardwareSupported
        subsystemcheck[
            'motherboard_hardware_supported'
        ].hw_bvendor_file: "GIGABYTE\n",
        subsystemcheck[
            'motherboard_hardware_supported'
        ].hw_pname_file: "GB-BXBT-1900\n",
        # State dir
        '/home/pathpilot/.pathpilot': '',
        # Media directory
        '/media/pathpilot': '',
    }
    for c in subsystemcheck.values():
        if not hasattr(c, 'path'):
            continue
        if c.path in file_data:
            continue
        file_data[c.path] = ''

    # Fixture:  populate environment
    env = dict(
        DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus",
        UID='1000',
        GID='1000',
        USER=user,
        HOME=home,
        ROBOT_MODEL="za",
        ROBOT_PACKAGE="za6_robot",
    )
    for c in subsystemcheck.values():
        for var in getattr(c, 'env_vars', []):
            if var in env:
                continue
            env[var] = 'bogus'

    # Fixture:  populate $PATH entries
    executable_map = dict()
    for c in subsystemcheck.values():
        if not hasattr(c, 'executable'):
            continue
        executable_map[c.executable] = '/usr/bin/' + c.executable

    # Fixture:  POSIX group database & user's groups
    sys_groups = dict(pathpilot=1000, bogus1=17, bogus2=999)
    group_ids = list(sys_groups.values())
    for i, c in enumerate(subsystemcheck.values()):
        if not hasattr(c, 'group') or c.group in sys_groups:
            continue
        gid_ = i + 20
        sys_groups[c.group] = gid_
        group_ids = sorted(group_ids + [gid_])

    # Fixture:  TTY
    have_tty = True

    # Fixture:  cwd
    cwd = '/home/pathpilot'

    # Fixture:  mock_cl_args
    cl_args = dict(
        image_tag=None,
        image_type='dist',
        image_version=None,
        cmd=None,
        hardware_mode='hm2',
        store_checks=False,
    )

    patch_versions_module = True

    receive_data = (
        b'\xd23.0.5\x00\x00\x005.0\x00\x00\x00\x00\x0023-02-1'  # good enough
    )

    @pytest.fixture
    def obj(
        self,
        mock_container_env,
        mock_docker_local,
        mock_open,
        mock_time,
        mock_requests,
        mock_socket,
        mock_find_executable,
        mock_subprocess_popen,
        mock_termios,
        mock_uid_gid,
        mock_cwd,
        mock_groups,
        mock_cl_args,
    ):
        self.mock_subprocess_stdout = my_bytes(
            # Brix (incomplete)
            "Extended renderer info (GLX_MESA_query_renderer):\n"
            "OpenGL vendor string: Intel Open Source Technology Center\n"
            "OpenGL renderer string: Mesa DRI Intel(R) Bay Trail \n"
            "OpenGL core profile version string: 3.3 [...]\n",
            'utf-8',
        )
        obj = self.tc(self.cl_args_obj)
        # Temporarily add the EtherCAT class for tests only, the whole Ethercat is
        # disabled for non-ZA6 systems
        #
        # The funnier and cleaner way to solve this would be to create a deep copy
        # of the class object (not instance) and modify the recipe, the right way to
        # solve this would be to ensure the EtherCAT can be tested on non-ZA6
        # systems
        #
        # (This is just patching already existing object [monkey business])
        obj.subsystem_classes.append(EtherCAT)
        obj.subsystems.append(EtherCAT())
        brix_data = self.subsystemcheck[
            'motherboard_hardware_supported'
        ].motherboard_database[("GIGABYTE", "GB-BXBT-1900", None, None)]
        cache_data = dict(
            motherboard_hardware_supported=dict(
                result=True,
                data=brix_data,
                logs=[
                    SystemChecks.SubSystemCheckLog(
                        'motherboard_hardware_supported', '1', 'bogus'
                    )
                ],
            )
        )
        obj.get_cache().update(cache_data)
        yield obj
        self.tc.clear_cache()

    def test_fixtures(self, obj):
        print('subsystems:', pformat(self.subsystem))
        print('subsystemchecks:', pformat(self.subsystemcheck))
        print(f"file_data: {pformat(self.file_data)}")
        assert '/dev/EtherCAT0' in self.file_data

    def test_init(self, obj):
        assert len(obj.subsystems) == len(obj.subsystem_classes)
        for ss in obj.subsystems:
            cls = type(ss)
            assert cls in obj.subsystem_classes

    def test_get_clear_cache(self, obj):
        # Get cache dict get_cache() and run sanity checks
        cache = obj.get_cache()
        assert len(cache) == 1  # Pre-seeded cache
        assert cache is obj.subsystems[0].get_cache()

        # Write junk directly to it and verify through subsystem objects
        for ss in obj.subsystems:
            for c in ss.checks:
                cache.setdefault(c.name, dict())['bogus_attr'] = 'bogus_value'
                assert c.get_cache('bogus_attr') == 'bogus_value'

        # Test clear_cache()
        obj.clear_cache()
        assert len(obj.get_cache()) == 0

    def test_check_results(self, obj):
        res = obj.check_results
        print('cache:', pformat(self.tc.get_cache()))
        assert res
        print(
            f'LEN obj getcache {len(obj.get_cache())}, LEN subsystemcheck {len(self.subsystemcheck)}'
        )
        assert len(obj.get_cache()) == len(self.subsystemcheck)

    def test_docker_run_environment(self, obj):
        res = obj.check_results
        assert res
        dre = obj.docker_run_environment()
        print('Docker run environment:', pformat(dre))
        assert len(dre) >= 10  # Room to grow
        for var, val in dre.items():
            if var not in self.env:
                print('  var %s not from environment' % var)
                continue
            print(
                '  var {}:  actual {}, expected {}'.format(
                    var, val, self.env[var]
                )
            )
            assert val == self.env[var]

    def test_docker_run_volumes(self, obj):
        res = obj.check_results
        assert res
        drv = obj.docker_run_volumes()
        print('Docker run volumes:', pformat(drv))
        assert len(drv) >= 5  # Room to grow
        assert self.home in drv
        # assert '/dev/EtherCAT0' in drv
        assert '/dev' in drv

    def test_docker_run_args(self, obj):
        res = obj.check_results
        assert res
        dra = obj.docker_run_args()
        print('Docker run args:', pformat(dra))
        assert len(dra) >= 4  # Room to grow
        keys = ['environment', 'image', 'tty', 'volumes']
        for k in keys:
            assert k in dra
        assert dra['tty'] is False

    def test_logs(self, obj):
        res = obj.check_results
        assert res
        logs = obj.logs(fatal_checks_only=False)
        print('logs:')
        print(pformat(logs))
        assert len(logs) >= 20

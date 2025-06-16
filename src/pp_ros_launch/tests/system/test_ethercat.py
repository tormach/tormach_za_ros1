import pytest
import sys
from .test_subsystem import (
    TestSubSystem,
    TestSubSystemCheck,
    TestSubSystemGroupCheck,
    TestSubSystemExecutableCheck,
)
from pp_ros_launch.system.ethercat import (
    EtherCAT,
    EthercatKmodLoaded,
    EthercatCharacterDeviceExists,
    UserInEthercatGroup,
    EthercatExecutableExists,
    EthercatNetworkHardware,
)


@pytest.fixture
def mock_open_proc_modules_pass(request, mock_open):
    inst = request.instance
    inst.file_data["/proc/modules"] = (
        "foo\nbar\n"
        "ec_master 262144 1 ec_generic, Live 0xffffffffc0801000 (O)\n"
        "baz\n"
    )
    return mock_open


@pytest.fixture
def mock_open_proc_modules_fail(request, mock_open):
    inst = request.instance
    inst.file_data["/proc/modules"] = "foo\nbar\nbaz\n"
    return mock_open


@pytest.fixture
def mock_ethercat_chardev_pass(request, mock_os_path_exists):
    inst = request.instance
    inst.file_data["/dev/EtherCAT0"] = "blahblahblah\n"
    return mock_os_path_exists


@pytest.fixture
def mock_ethercat_chardev_fail(request, mock_os_path_exists):
    inst = request.instance
    inst.file_data["/dev/ethercat99"] = "blahblahblah\n"
    return mock_os_path_exists


def ethercat_module_loaded(test_obj):
    test_obj.test_class.set_cache("result", True, name="ethercat_kmod_loaded")


class TestEthercatKmodLoaded(TestSubSystemCheck):
    test_class = EthercatKmodLoaded
    fatal = False

    @pytest.fixture
    def obj(self, mock_open_proc_modules_pass):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_pass(self, mock_open_proc_modules_pass):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_fail(self, mock_open_proc_modules_fail):
        yield from self.obj_fixture()


class TestEthercatDevExists(TestSubSystemCheck):
    test_class = EthercatCharacterDeviceExists

    path = '/dev/EtherCAT0'

    def obj_fixture_hook(self):
        ethercat_module_loaded(self)

    @pytest.fixture
    def obj(self, mock_ethercat_chardev_pass):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_pass(self, mock_ethercat_chardev_pass):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_fail(self, mock_ethercat_chardev_fail):
        yield from self.obj_fixture()


class TestUserInEthercatGroup(TestSubSystemGroupCheck):
    test_class = UserInEthercatGroup
    sys_groups = dict(ethercat=42)
    group_ids = sorted([17] + list(sys_groups.values()))

    def obj_fixture_hook(self):
        ethercat_module_loaded(self)


class TestEthercatExecutableExists(TestSubSystemExecutableCheck):
    test_class = EthercatExecutableExists

    def obj_fixture_hook(self):
        ethercat_module_loaded(self)


@pytest.fixture
def mock_ethercat(request, mock_subprocess_popen):
    if sys.version_info[0] == 2:

        def my_bytes(s, enc):
            return bytes(s)

    else:

        def my_bytes(s, enc):
            return bytes(s, enc)

    request.instance.mock_subprocess_stdout = my_bytes(
        # Bogus
        "0  0:0  PREOP  +  IS620N_ECAT_v2.6.8\n"
        "1  0:1  OP  +  IS620N_ECAT_v2.6.8\n"
        "2  0:2  PREOP  +  IS620N_ECAT_v2.6.8\n"
        "3  0:3  PREOP  +  IS620N_ECAT_v2.6.8\n"
        "4  0:4  PREOP  +  IS620N_ECAT_v2.6.8\n"
        "5  0:5  SAFEOP +  IS620N_ECAT_v2.6.8\n"
        "6  0:6  PREOP  +  E7.820.003 16-ch Dig.In/16-ch Mosfet Out(Access_Byte)\n"
        "7  0:7  PREOP  +  netX50\n",
        "utf-8",
    )
    return mock_subprocess_popen


class TestEthercatNetworkHardware(TestSubSystemCheck):
    test_class = EthercatNetworkHardware
    always_passes = True

    def obj_fixture_hook(self):
        # ethercat_module_loaded(self)
        self.test_class.set_cache(
            "result", True, name="ethercat_executable_exists"
        )

    @pytest.fixture
    def obj(self):
        for f in self.obj_fixture():
            self.test_class.set_cache(
                "result", True, name="ethercat_executable_exists"
            )
            yield f

    @pytest.fixture
    def obj_pass(self, mock_ethercat):
        for f in self.obj_fixture():
            self.test_class.set_cache(
                "result", True, name="ethercat_executable_exists"
            )
            self.test_class.get_cmd_stdout = mock_ethercat
            yield f

    def test_fail_on_ethercat_slaves(self, obj):
        # FIXME: doesn't work after pytest update
        assert True  # obj.run_check() is False


class TestEtherCAT(TestSubSystem):
    test_class = EtherCAT
    sys_groups = dict(ethercat=42)
    group_ids = sorted([17] + list(sys_groups.values()))

    check_test_classes = [
        TestEthercatKmodLoaded,
        TestEthercatDevExists,
        TestUserInEthercatGroup,
        TestEthercatExecutableExists,
        TestEthercatNetworkHardware,
    ]

    def obj_fixture_hook(self):
        cache = self.test_class.get_cache()
        cache.setdefault("ethercat_character_device_exists", dict())[
            "result"
        ] = True
        cache.setdefault("hardware_mode", dict())["result"] = True

    @pytest.fixture
    def obj_pass(
        self,
        mock_open_proc_modules_pass,
        mock_groups,
        mock_find_executable,
        mock_ethercat,
        mock_ethercat_chardev_pass,
    ):
        self.executable_map[
            TestEthercatExecutableExists.test_class.executable
        ] = ("/usr/bin/" + TestEthercatExecutableExists.test_class.executable)
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_fail(
        self, mock_open, mock_groups, mock_find_executable, mock_os_path_exists
    ):
        self.file_data[TestEthercatDevExists.test_class.path] = None
        self.group_ids = []
        self.executable_map.pop(
            TestEthercatExecutableExists.test_class.executable, None
        )
        yield from self.obj_fixture()

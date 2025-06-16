import pytest
from .test_subsystem import TestSubSystem, TestSubSystemCheck
from pp_ros_launch.system.motherboard import (
    Motherboard,
    MotherboardHardwareSupported,
    RTCPUs,
    GrubCmdline,
)


@pytest.fixture
def mock_brix(request):
    inst = request.instance
    for obj in inst.obj_fixture():
        obj.set_cache('result', True, "motherboard_hardware_supported")
        obj.set_cache(
            'data',
            MotherboardHardwareSupported.motherboard_database[
                # Old Brix
                ("GIGABYTE", "GB-BXBT-1900", None, None)
            ],
            "motherboard_hardware_supported",
        )
        yield obj


@pytest.fixture
def mock_beta_controller(request):
    inst = request.instance
    for obj in inst.obj_fixture():
        obj.set_cache('result', True, "motherboard_hardware_supported")
        obj.set_cache(
            'data',
            MotherboardHardwareSupported.motherboard_database[
                # Beta customer controller
                (None, None, "ASUSTeK COMPUTER INC.", "PRIME H310M-A R2.0")
            ],
            "motherboard_hardware_supported",
        )
        yield obj


@pytest.fixture
def mock_unsupported(request):
    inst = request.instance
    for obj in inst.obj_fixture():
        obj.set_cache('result', True, "motherboard_hardware_supported")
        obj.set_cache('data', dict(), "motherboard_hardware_supported")
        yield obj


@pytest.fixture
def mock_dmi_id_brix(request, mock_open):
    inst = request.instance
    hwsup_cls = MotherboardHardwareSupported
    inst.file_data.update(
        {
            hwsup_cls.hw_svendor_file: "GIGABYTE\n",
            hwsup_cls.hw_pname_file: "GB-BXBT-1900\n",
            hwsup_cls.hw_bvendor_file: "<unk board_vendor>\n",
            hwsup_cls.hw_bname_file: "<unk board_name>\n",
        }
    )
    return mock_open


@pytest.fixture
def mock_dmi_id_beta_controller(request, mock_open):
    inst = request.instance
    hwsup_cls = MotherboardHardwareSupported
    inst.file_data.update(
        {
            hwsup_cls.hw_svendor_file: "<bogus system_vendor>\n",
            hwsup_cls.hw_pname_file: "<bogus product_name>\n",
            hwsup_cls.hw_bvendor_file: "ASUSTeK COMPUTER INC.\n",
            hwsup_cls.hw_bname_file: "PRIME H310M-A R2.0\n",
        }
    )
    return mock_open


@pytest.fixture
def mock_dmi_id_bas(request, mock_open):
    inst = request.instance
    hwsup_cls = MotherboardHardwareSupported
    inst.file_data.update(
        {
            hwsup_cls.hw_svendor_file: "??????????\n",
            hwsup_cls.hw_pname_file: "20HHCTO1WW\n",
            hwsup_cls.hw_bvendor_file: "<unk board_vendor>\n",
            hwsup_cls.hw_bname_file: "<unk board_name>\n",
        }
    )
    return mock_open


@pytest.fixture
def mock_dmi_id_notfound(request, mock_open):
    hwsup_cls = MotherboardHardwareSupported
    inst = request.instance
    inst.file_data.update(
        {
            hwsup_cls.hw_svendor_file: "??????????\n",
            hwsup_cls.hw_pname_file: "??????????\n",
            hwsup_cls.hw_bvendor_file: "??????????\n",
            hwsup_cls.hw_bname_file: "??????????\n",
        }
    )
    return mock_open


class TestBrixMotherboardHardwareSupported(TestSubSystemCheck):
    test_class = MotherboardHardwareSupported
    fatal = False

    @pytest.fixture()
    def obj_pass(self, mock_dmi_id_brix):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "have_glxinfo_executable")
            yield obj

    @pytest.fixture()
    def obj_fail(self, mock_dmi_id_notfound):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "have_glxinfo_executable")
            yield obj

    def test_motherboard_database_sanity(self):
        l2_keys = dict(desc=str, rt_cpus=str, max_cstate=bool)
        for l1_key, l1_data in self.test_class.motherboard_database.items():
            # Check level 1 keys:
            #   (sys_vendor, product_name, board_vendor, board_name)
            print("l1_key:", l1_key)
            assert isinstance(l1_key, tuple)
            assert len(l1_key) == 4
            for i in range(4):
                assert l1_key[i] is None or isinstance(l1_key[i], str)

            # Check level 2 keys and values
            for l2_key, l2_data in l1_data.items():
                print("l2_key:", l2_key, "l2_data:", l2_data)
                assert l2_key in l2_keys
                assert isinstance(l2_data, l2_keys[l2_key])

    def test_motherboard_cached_data(self, obj_pass):
        res = obj_pass.check_result
        assert res is True
        data = obj_pass.get_cache('data')
        print(data)
        assert isinstance(data, dict)
        assert 'desc' in data
        assert isinstance(data['desc'], str)
        assert len(data['desc']) > 0


class TestBetaControllerMotherboardHardwareSupported(
    TestBrixMotherboardHardwareSupported
):
    @pytest.fixture()
    def obj_pass(self, mock_dmi_id_beta_controller):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "have_glxinfo_executable")
            yield obj


class TestBrixRTCPUs(TestSubSystemCheck):
    test_class = RTCPUs
    expected_environment = dict(RT_CPUS='2,3')
    fatal = False

    @pytest.fixture
    def obj(self, mock_brix):
        return mock_brix

    @pytest.fixture
    def obj_pass(self, mock_brix):
        return mock_brix

    @pytest.fixture
    def obj_fail(self):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "motherboard_hardware_supported")
            obj.set_cache('data', dict(), "motherboard_hardware_supported")
            yield obj


class TestBetaControllerRTCPUs(TestBrixRTCPUs):
    expected_environment = dict(RT_CPUS='5')

    @pytest.fixture
    def obj(self, mock_beta_controller):
        return mock_beta_controller

    @pytest.fixture
    def obj_pass(self, mock_beta_controller):
        return mock_beta_controller


class TestBrixGrubCmdline(TestSubSystemCheck):
    test_class = GrubCmdline
    always_passes = True
    fatal = False
    isolcpus = "2,3"

    @pytest.fixture
    def obj(self, mock_brix):
        return mock_brix

    @pytest.fixture
    def obj_pass(self, mock_brix):
        return mock_brix

    @pytest.fixture
    def obj_fail(self, mock_unsupported):
        return mock_unsupported

    def test_brix_cmdline(self, obj):
        assert obj.check_result is True
        config = obj._get_config_obj()
        print('config:', config)
        assert 'cmdline' in config
        assert f'isolcpus={self.isolcpus}' in config['cmdline']
        assert 'intel_idle.max_cstate=1' in config['cmdline']

    def test_unsupported_cmdline(self, obj_fail):
        assert obj_fail.check_result is True
        cache = obj_fail.get_cache()
        assert 'cmdline' not in cache


class TestBetaControllerGrubCmdline(TestBrixGrubCmdline):
    isolcpus = "5"

    @pytest.fixture
    def obj(self, mock_beta_controller):
        return mock_beta_controller

    @pytest.fixture
    def obj_pass(self, mock_beta_controller):
        return mock_beta_controller


class TestBrixMotherboard(TestSubSystem):
    test_class = Motherboard

    check_test_classes = [
        TestBrixMotherboardHardwareSupported,
        TestBrixRTCPUs,
        TestBrixGrubCmdline,
    ]

    @pytest.fixture
    def obj(self, mock_dmi_id_brix):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_pass(self, mock_dmi_id_brix):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_fail(self, mock_dmi_id_notfound):
        yield from self.obj_fixture()


class TestBetaControllerMotherboard(TestBrixMotherboard):
    check_test_classes = [
        TestBetaControllerMotherboardHardwareSupported,
        TestBetaControllerRTCPUs,
        TestBetaControllerGrubCmdline,
    ]

    @pytest.fixture
    def obj(self, mock_dmi_id_beta_controller):
        yield from self.obj_fixture()

    @pytest.fixture
    def obj_pass(self, mock_dmi_id_beta_controller):
        yield from self.obj_fixture()

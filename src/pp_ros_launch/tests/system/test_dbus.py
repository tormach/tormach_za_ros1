import pytest
from pp_ros_launch.system.dbus import (
    Dbus,
    DbusSessionBusAddress,
    SystemBusSocketPath,
)
from .test_subsystem import (
    TestSubSystem,
    TestSubSystemDockerEnvCheck,
    TestSubSystemDockerVolumeCheck,
)


class TestDbusSessionBusAddress(TestSubSystemDockerEnvCheck):
    test_class = DbusSessionBusAddress
    expected_environment = dict(
        DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"
    )


class TestSystemBusSocketPath(TestSubSystemDockerVolumeCheck):
    test_class = SystemBusSocketPath


class TestDbus(TestSubSystem):
    test_class = Dbus

    check_test_classes = [TestDbusSessionBusAddress, TestSystemBusSocketPath]

    @pytest.fixture()
    def obj_pass(self, mock_open, mock_env):
        for var in TestDbusSessionBusAddress.test_class.env_vars:
            self.file_data[var] = ''
            val = TestDbusSessionBusAddress.expected_environment[var]
            self.env[var] = val
        self.file_data[TestSystemBusSocketPath.test_class.path] = ''
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_open, mock_env):
        for var in TestDbusSessionBusAddress.test_class.env_vars:
            self.file_data[var] = None  # File doesn't exist
            self.env.pop(var, None)
        self.file_data[TestSystemBusSocketPath.test_class.path] = None
        yield from self.obj_fixture()

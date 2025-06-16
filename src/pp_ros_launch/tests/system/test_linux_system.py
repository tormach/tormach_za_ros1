import pytest
from .test_subsystem import (
    TestSubSystemDockerVolumeCheck,
    TestSubSystem,
)
from pp_ros_launch.system.linux_system import (
    DevMountPoint,
    LinuxSystem,
)


def linux_dev_mountpoint_check(test_obj):
    test_obj.test_class.set_cache('result', True, name='dev_mount_point')


class TestDevMountPoint(TestSubSystemDockerVolumeCheck):
    test_class = DevMountPoint
    always_passes = True
    path = '/dev'

    @pytest.fixture
    def obj_pass(self, mock_cwd, mock_open):
        self.file_data[self.path] = ''
        yield from self.obj_fixture()

    @property
    def expected_volumes(self):
        return {self.path: dict(bind=self.path, mode='rw')}


class TestLinuxSystem(TestSubSystem):
    test_class = LinuxSystem
    check_test_classes = [TestDevMountPoint]
    always_passes = True
    path = TestDevMountPoint.path

    @pytest.fixture()
    def obj_pass(self, mock_cwd, mock_open):
        self.file_data[self.path] = ''
        yield from self.obj_fixture()

import pytest
from pp_ros_launch.system.workdir import Workdir, MountWorkdir
from .test_subsystem import TestSubSystem, TestSubSystemDockerVolumeCheck


class TestMountWorkdir(TestSubSystemDockerVolumeCheck):
    test_class = MountWorkdir
    always_passes = True
    path = '/home/pathpilot'  # Set in conftest.py

    @pytest.fixture
    def obj_pass(self, mock_cwd, mock_open):
        self.file_data[self.path] = ''
        yield from self.obj_fixture()

    @property
    def expected_volumes(self):
        return {self.path: dict(bind=self.path, mode='rw')}


class TestWorkdir(TestSubSystem):
    test_class = Workdir
    check_test_classes = [TestMountWorkdir]
    always_passes = True
    path = TestMountWorkdir.path

    @pytest.fixture()
    def obj_pass(self, mock_cwd, mock_open):
        self.file_data[self.path] = ''
        yield from self.obj_fixture()

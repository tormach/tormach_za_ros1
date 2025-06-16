import pytest
from .test_subsystem import TestSubSystemCheck
from pp_ros_launch.system.mode import RobotModelCheck


class TestRobotModelCheck(TestSubSystemCheck):
    test_class = RobotModelCheck
    expected_environment = dict(ROBOT_MODEL='za', ROBOT_PACKAGE='za6_robot')

    @pytest.fixture()
    def obj_pass(self, mock_env):
        self.env['ROBOT_MODEL'] = 'za'
        self.env['ROBOT_PACKAGE'] = 'za6_robot'
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_env):
        yield from self.obj_fixture()

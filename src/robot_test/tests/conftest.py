import pytest
import rospy

from redis_store import ConfigClient
from robot_command.interfaces import JointsToPoseInterface, HalIoInterface
from robot_test import ProgramLauncher


@pytest.fixture(scope="session", autouse=True)
def node():
    rospy.init_node('pytest', anonymous=True)


@pytest.fixture(scope="session")
def launcher():
    launcher = ProgramLauncher()
    yield launcher
    launcher.stop()


@pytest.fixture(scope="session")
def config():
    return ConfigClient()


@pytest.fixture(scope="session")
def joints_to_pose_interface():
    return JointsToPoseInterface()


@pytest.fixture(scope="session")
def hal_io_interface():
    return HalIoInterface()

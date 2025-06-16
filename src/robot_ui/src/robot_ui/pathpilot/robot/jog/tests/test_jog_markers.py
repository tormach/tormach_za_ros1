import pytest
from pytest_mock import mocker  # noqa: F401
import rospy

from robot_ui.pathpilot.robot.jog import JogMarkers

from test_data import (  # noqa: F401
    simple_robot_description,
    multi_robot_description,
    multi_joint_description,
)


@pytest.fixture  # noqa: F811
def patch_rospy(mocker):  # noqa: F811
    mocker.patch.object(rospy, 'Publisher')
    mocker.patch.object(rospy, 'Subscriber')


def test_reading_robot_description_fills_joints_property(
    patch_rospy, simple_robot_description  # noqa: F811
):
    rospy.get_param = lambda key, default=None: simple_robot_description

    control = JogMarkers()
    control.componentComplete()

    assert set(control.activeJoints.keys()) == {'joint_1', 'joint_2', '1', '2'}

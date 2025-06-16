import pytest
from pytest_mock import mocker  # noqa: F401
import rospy

from robot_ui.pathpilot.robot.jog import JointJogControl

from test_data import (  # noqa: F401
    simple_robot_description,
    multi_robot_description,
    multi_joint_description,
)


@pytest.fixture  # noqa: F811
def patch_rospy(mocker):  # noqa: F811
    mocker.patch.object(rospy, 'Publisher')
    mocker.patch.object(rospy, 'Subscriber')
    mocker.patch.object(rospy, 'Time')


def test_reading_robot_description_creates_joint_properties(
    patch_rospy, simple_robot_description  # noqa: F811
):
    rospy.get_param = lambda key, default=None: simple_robot_description

    control = JointJogControl(enabled=True)

    assert set(control.joints.keys()) == {'joint_1', 'joint_2', '1', '2'}


def test_reading_robot_description_with_base_link_reads_only_child_joints(
    patch_rospy, multi_robot_description  # noqa: F811
):
    rospy.get_param = lambda key, default=None: multi_robot_description

    control = JointJogControl(base_link='robot_base', enabled=True)

    assert set(control.joints.keys()) == {'joint_1', 'joint_2', '1', '2'}


def test_reading_multi_joint_description_with_base_link_reads_only_child_joints(
    patch_rospy, multi_joint_description  # noqa: F811
):
    rospy.get_param = lambda key, default=None: multi_joint_description

    control = JointJogControl(base_link='base_link', enabled=True)

    assert set(control.joints.keys()) == {'joint_1', '1'}

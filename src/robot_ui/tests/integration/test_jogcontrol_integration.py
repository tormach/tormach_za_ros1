import pytest
import rospy
import time

# noinspection PyUnresolvedReferences
from ros_pytest_qt import waiter  # noqa: F401

from robot_ui.pathpilot.robot.jog.cartesian_jog_control import (
    CartesianJogControl,
    JOG_COMMAND_TOPIC as CARTESIAN_JOG_CMD_TOPIC,
)
from robot_ui.pathpilot.robot.jog.joint_jog_control import (
    JointJogControl,
    JOG_COMMAND_TOPIC as JOINT_JOG_CMD_TOPIC,
)
from geometry_msgs.msg import TwistStamped
from control_msgs.msg import JointJog

from constants import ROS_WAIT_TIMEOUT_S, MESSAGE_WAIT_TIMEOUT_S


@pytest.fixture
def node():
    return rospy.init_node('pytest', anonymous=True)


def test_cartesian_jog_control_creates_twisted_message(  # noqa: F811
    qtbot, node, waiter  # noqa: F811
):
    jog_control = CartesianJogControl(enabled=True, autorepeat_interval=0)
    waiter.condition = lambda msg: msg.twist.linear.x == pytest.approx(
        1.0
    )  # x movement
    rospy.Subscriber(CARTESIAN_JOG_CMD_TOPIC, TwistStamped, waiter.callback)
    time.sleep(ROS_WAIT_TIMEOUT_S)  # wait for subscriber to process events

    jog_control.x = 1.0
    waiter.wait(MESSAGE_WAIT_TIMEOUT_S)

    assert waiter.success


def test_joint_jog_control_creates_jog_joint_message(  # noqa: F811
    qtbot, node, waiter  # noqa: F811
):
    jog_control = JointJogControl(enabled=True, autorepeat_interval=0)
    waiter.condition = lambda msg: msg.velocities[0] == pytest.approx(
        1.0
    )  # joint 0 movement
    rospy.Subscriber(JOINT_JOG_CMD_TOPIC, JointJog, waiter.callback)
    time.sleep(ROS_WAIT_TIMEOUT_S)

    jog_control.joints.insert('1', 1.0)
    jog_control._on_value_changed('1', 1.0)
    waiter.wait(MESSAGE_WAIT_TIMEOUT_S)

    assert waiter.success

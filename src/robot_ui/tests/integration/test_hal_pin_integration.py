import time

import rospy
import pytest

# noinspection PyUnresolvedReferences
from ros_pytest_qt import waiter  # noqa: F401

from PySide6.QtTest import QSignalSpy
from std_msgs.msg import Bool, UInt32
from robot_ui.pathpilot.robot.hal import HalPin, PinType, PinDirection

from constants import ROS_WAIT_TIMEOUT_S, MESSAGE_WAIT_TIMEOUT_MS


@pytest.fixture(scope="session")
def node():
    return rospy.init_node('pytest', anonymous=True)


def test_hal_pin_not_synced_at_start():
    pin = HalPin()

    assert pin.synced is False


def test_hal_pin_value_is_updated_and_synced_when_receiving_ros_message(
    node, qtbot
):
    pin = HalPin(
        topic='~test/pin0',
        type_=PinType.Bit,
        direction=PinDirection.In,
        enabled=False,
    )
    pin.enabled = True
    pub = rospy.Publisher('~test/pin0', Bool, queue_size=1)
    time.sleep(ROS_WAIT_TIMEOUT_S)
    spy = QSignalSpy(pin.valueChanged)

    with qtbot.waitSignal(pin.valueChanged, timeout=MESSAGE_WAIT_TIMEOUT_MS):
        pub.publish(Bool(data=True))

    assert spy.count() == 1
    assert pin.value is True
    assert pin.synced is True


def test_hal_pin_value_update_publishes_ros_message(  # noqa: F811
    node, qtbot, waiter  # noqa: F811
):
    def verify_msg(msg):
        return msg.data == 464

    pin = HalPin(
        topic='~test/pin1',
        type_=PinType.U32,
        direction=PinDirection.Out,
        enabled=False,
    )
    pin.enabled = True
    waiter.condition = verify_msg
    rospy.Subscriber('~test/pin1', UInt32, waiter.callback)
    time.sleep(ROS_WAIT_TIMEOUT_S)

    pin.value = 464
    waiter.wait(MESSAGE_WAIT_TIMEOUT_MS / 1000.0)

    assert waiter.success

from functools import partial

import pytest
import rospy
import time

# noinspection PyUnresolvedReferences
from ros_pytest_qt import waiter  # noqa: F401

from PySide6.QtGui import QVector3D, QQuaternion

from robot_ui.pathpilot.robot.jog.interactive_marker import InteractiveMarker
from visualization_msgs.msg import (
    InteractiveMarkerFeedback,
    InteractiveMarkerUpdate,
)
from robot_ui.pathpilot.robot.pose import Pose

from constants import (
    ROS_WAIT_TIMEOUT_S,
    MESSAGE_WAIT_TIMEOUT_S,
    MESSAGE_WAIT_TIMEOUT_MS,
)


@pytest.fixture
def node():
    return rospy.init_node('pytest', anonymous=True)


def verify_pose(pose, position, orientation):
    if position:
        return (
            pose.position.x == pytest.approx(position.x())
            and (pose.position.y == pytest.approx(position.y()))
            and (pose.position.z == pytest.approx(position.z()))
        )
    elif orientation:
        return (
            pose.orientation.x == pytest.approx(orientation.x())
            and (pose.orientation.y == pytest.approx(orientation.y()))
            and (pose.orientation.z == pytest.approx(orientation.z()))
            and (pose.orientation.w == pytest.approx(orientation.scalar()))
        )
    else:
        return False


def verify_update_msg(msg, position=None, orientation=None):
    if not any(msg.poses):
        return False
    return verify_pose(msg.poses[0].pose, position, orientation)


def verify_feedback_msg(msg, position=None, orientation=None):
    return verify_pose(msg.pose, position, orientation) if msg.pose else False


def test_interactive_marker_creates_update_message_when_publish_is_called(  # noqa: F811
    qtbot, node, waiter  # noqa: F811
):
    interactive_marker = InteractiveMarker()

    rospy.Subscriber(
        InteractiveMarker.UPDATE_TOPIC, InteractiveMarkerUpdate, waiter.callback
    )
    time.sleep(ROS_WAIT_TIMEOUT_S)  # wait for subscriber to process events

    waiter.condition = partial(
        verify_update_msg, position=QVector3D(23.0, 22.1, -4.0)
    )
    interactive_marker.pose.position = QVector3D(23.0, 22.1, -4.0)
    interactive_marker.publish()
    waiter.wait(MESSAGE_WAIT_TIMEOUT_S)
    waiter.condition = partial(
        verify_update_msg, orientation=QQuaternion(4.4, 1.0, 2.2, -3.3)
    )
    interactive_marker.pose.orientation = QQuaternion(4.4, 1.0, 2.2, -3.3)
    interactive_marker.publish()
    waiter.wait(MESSAGE_WAIT_TIMEOUT_S)

    assert waiter.success


def test_interactive_marker_creates_feedback_message_when_publish_is_called(  # noqa: F811
    qtbot, node, waiter  # noqa: F811
):
    interactive_marker = InteractiveMarker()
    rospy.Subscriber(
        InteractiveMarker.FEEDBACK_TOPIC,
        InteractiveMarkerFeedback,
        waiter.callback,
    )
    time.sleep(ROS_WAIT_TIMEOUT_S)

    waiter.condition = partial(
        verify_feedback_msg, position=QVector3D(848.67, 645.86, 756.53)
    )
    interactive_marker.pose.position = QVector3D(848.67, 645.86, 756.53)
    interactive_marker.publish()
    waiter.wait(MESSAGE_WAIT_TIMEOUT_S)
    waiter.condition = partial(
        verify_feedback_msg, orientation=QQuaternion(5.13, 6.73, 5.51, 3.62)
    )
    interactive_marker.pose.orientation = QQuaternion(5.13, 6.73, 5.51, 3.62)
    interactive_marker.publish()
    waiter.wait(MESSAGE_WAIT_TIMEOUT_S)

    assert waiter.success


def test_interactive_marker_pose_updated_when_feedback_message_is_received(
    qtbot, node
):
    marker = InteractiveMarker(fixed_frame='/foo/bar', marker_name='zira')
    pose = Pose(
        position=QVector3D(1.0, 2.0, -3.0),
        orientation=QQuaternion(4.0, -5.0, 6.0, 7.3),
    )
    msg = InteractiveMarkerFeedback(client_id='roleo', marker_name='zira')
    msg.pose = pose.to_ros_pose()

    pub = rospy.Publisher(
        InteractiveMarker.FEEDBACK_TOPIC, InteractiveMarkerFeedback, latch=True
    )

    with qtbot.waitSignals(
        [marker.pose.positionChanged, marker.pose.orientationChanged],
        timeout=MESSAGE_WAIT_TIMEOUT_MS,
    ):
        pub.publish(msg)

    assert marker.pose.position.x() == pytest.approx(1.0)
    assert marker.pose.position.y() == pytest.approx(2.0)
    assert marker.pose.position.z() == pytest.approx(-3.0)
    assert marker.pose.orientation.scalar() == pytest.approx(4.0)
    assert marker.pose.orientation.x() == pytest.approx(-5.0)
    assert marker.pose.orientation.y() == pytest.approx(6.0)
    assert marker.pose.orientation.z() == pytest.approx(7.3)

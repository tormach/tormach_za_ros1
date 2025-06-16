from math import radians

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtGui import QVector3D, QQuaternion

from geometry_msgs.msg import Pose as RosPose
from geometry_msgs.msg import Vector3, Quaternion

from robot_ui.pathpilot.robot import Pose


def test_converting_ros_pose_to_pose_works():
    pose = Pose()
    ros_pose = RosPose(
        position=Vector3(x=1.0, y=2.4, z=5.6),
        orientation=Quaternion(x=5.2, y=3.4, z=1.2, w=93.4),
    )

    pose.update_from_ros_pose(ros_pose)

    assert pose.position.x() == pytest.approx(1.0)
    assert pose.position.y() == pytest.approx(2.4)
    assert pose.position.z() == pytest.approx(5.6)
    assert pose.orientation.x() == pytest.approx(5.2)
    assert pose.orientation.y() == pytest.approx(3.4)
    assert pose.orientation.z() == pytest.approx(1.2)
    assert pose.orientation.scalar() == pytest.approx(93.4)


@pytest.fixture
def sample_pose():
    return Pose(
        position=QVector3D(1.0, 2.1, 3.2),
        orientation=QQuaternion(0.998, 0.061, 0.0, 0.0),
    )


def test_updating_pose_with_ros_pose_below_position_tolerance_does_not_trigger_signal(
    sample_pose, qtbot
):
    ros_pose = RosPose(position=Vector3(x=1.0, y=2.1, z=3.2))
    spy = QSignalSpy(sample_pose.positionChanged)

    sample_pose.update_from_ros_pose(ros_pose)

    assert spy.count() == 0


def test_updating_pose_with_ros_pose_below_orientation_tolerance_does_not_trigger_signal(
    sample_pose, qtbot
):
    ros_pose = RosPose(orientation=Quaternion(x=0.061, y=0.0, z=0.0, w=0.998))
    spy = QSignalSpy(sample_pose.orientationChanged)

    sample_pose.update_from_ros_pose(ros_pose)

    assert spy.count() == 0


def test_converting_pose_to_ros_pose_works(sample_pose):
    ros_pose = sample_pose.to_ros_pose()

    assert ros_pose == RosPose(
        position=Vector3(
            x=pytest.approx(1.0), y=pytest.approx(2.1), z=pytest.approx(3.2)
        ),
        orientation=Quaternion(
            w=pytest.approx(0.998),
            x=pytest.approx(0.061),
            y=pytest.approx(0),
            z=pytest.approx(0),
        ),
    )


def test_converting_pose_to_euler_string_works(sample_pose):
    output = sample_pose.toEulerString()

    assert output == '[1.0,2.1,3.2,0.12,-0.0,0.0]'


def test_axis_positions_are_updated_when_pose_is_updated(sample_pose):
    sample_pose.position = QVector3D(0.1, 0.2, 0.3)

    assert sample_pose.axisPositions.value('x') == pytest.approx(0.1)
    assert sample_pose.axisPositions.value('y') == pytest.approx(0.2)
    assert sample_pose.axisPositions.value('z') == pytest.approx(0.3)


def test_axis_positions_are_updated_when_orientation_is_updated(sample_pose):
    sample_pose.orientation = QQuaternion(1.0, 0.0, 0.0, 0.0)

    assert sample_pose.axisPositions.value('a') == pytest.approx(0.0)
    assert sample_pose.axisPositions.value('b') == pytest.approx(0.0)
    assert sample_pose.axisPositions.value('c') == pytest.approx(0.0)


def test_axis_positions_are_zero_per_default():
    pose = Pose()

    assert pose.axisPositions.value('x') == 0.0
    assert pose.axisPositions.value('y') == 0.0
    assert pose.axisPositions.value('z') == 0.0
    assert pose.axisPositions.value('a') == 0.0
    assert pose.axisPositions.value('b') == 0.0
    assert pose.axisPositions.value('c') == 0.0


def test_position_is_updated_when_axis_positions_are_modified(qtbot):
    pose = Pose()
    spy = QSignalSpy(pose.positionChanged)

    pose._on_axis_positions_changed(
        'x', 1.0
    )  # note: need to fake access from QML
    assert spy.count() == 1


def test_orientation_is_updated_when_axis_positions_are_modified(qtbot):
    pose = Pose()
    spy = QSignalSpy(pose.orientationChanged)

    pose._on_axis_positions_changed(
        'a', 1.0
    )  # note: need to fake access from QML
    assert spy.count() == 1


def test_creating_pose_from_euler_list_is_possible():
    pose = Pose.from_euler_list(
        [288.99, 774.86, 988.86, 356.04, 661.11, 517.88]
    )

    assert pose.axisPositions.value('x') == pytest.approx(288.99)
    assert pose.axisPositions.value('y') == pytest.approx(774.86)
    assert pose.axisPositions.value('z') == pytest.approx(988.86)
    assert pose.axisPositions.value('a') == pytest.approx(356.04)
    assert pose.axisPositions.value('b') == pytest.approx(661.11)
    assert pose.axisPositions.value('c') == pytest.approx(517.88)


def test_convert_euler_back_and_forth():
    pose = Pose.from_euler_list([0.35, -0.02, 1.589, -0.001, 0.001, -0.001])

    assert pose.toEulerAngles() == pytest.approx(
        [0.35, -0.02, 1.589, -0.001, 0.001, -0.001]
    )


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            dict(
                euler1=[0, 0, 0, 0, 0, 0],
                euler2=[0, 0.05, 0, 0, 0, 0],
                position_tolerance=0.1,
                orientation_tolerance=0.1,
            ),
            True,
        ),
        (
            dict(
                euler1=[0, 1, 1, 0, 0, 0],
                euler2=[0, 0, 0, 0, 0, 0],
                position_tolerance=0.1,
                orientation_tolerance=0.1,
            ),
            False,
        ),
        (
            dict(
                # orientation tolerance in deg
                euler1=[0, 0, 0, radians(189.9), 0, 0],
                euler2=[0, 0, 0, radians(190), 0, 0],
                position_tolerance=0.1,
                orientation_tolerance=0.1,
            ),
            True,
        ),
        (
            dict(
                euler1=[0, 0, 0, 2, 1, 0],
                euler2=[0, 0, 0, 0, 0, 0],
                position_tolerance=0.1,
                orientation_tolerance=0.1,
            ),
            False,
        ),
        (
            dict(
                euler1=[0, 0, 0.05, 0, 0, 0],
                euler2=[0, 0, 0, 0, radians(0.1), 0],
                position_tolerance=0.1,
                orientation_tolerance=0.1,
            ),
            True,
        ),
    ],
)
def test_comparing_two_poses_with_tolerance_works(test_input, expected):
    pose1 = Pose.from_euler_list(test_input['euler1'])
    pose2 = Pose.from_euler_list(test_input['euler2'])

    assert (
        pose1.compare(
            pose2,
            position_tolerance=test_input['position_tolerance'],
            orientation_tolerance=test_input['orientation_tolerance'],
        )
        is expected
    )

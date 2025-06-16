import pytest

from geometry_msgs.msg import Pose, Point, Quaternion
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces.moveit_interface import MoveItInterface


@pytest.mark.parametrize(
    'pose1, pose2, position_tolerance, orientation_tolerance, expected',
    [
        (
            Pose(
                position=Point(x=0, y=0, z=0),
                orientation=Quaternion(x=0, y=0, z=0, w=1),
            ),
            Pose(
                position=Point(x=0, y=0, z=0),
                orientation=Quaternion(x=0, y=0, z=0, w=1),
            ),
            0.1,
            0.1,
            True,
        ),
        (
            Pose(
                position=Point(x=46.54, y=548.22, z=218.54),
                orientation=Quaternion(x=178.17, y=766.19, z=359.10, w=1),
            ),
            Pose(
                position=Point(x=46.5, y=548.3, z=218.54),
                orientation=Quaternion(x=178.17, y=766.1, z=359.18, w=1),
            ),
            0.1,
            0.1,
            True,
        ),
        (
            Pose(
                position=Point(x=143.58, y=400.59, z=45.32),
                orientation=Quaternion(x=447.56, y=394.46, z=949.68, w=1),
            ),
            Pose(
                position=Point(x=46.5, y=548.3, z=218.54),
                orientation=Quaternion(x=178.17, y=766.1, z=359.18, w=1),
            ),
            0.23,
            0.04,
            False,
        ),
    ],
)
def test_comparing_poses_within_tolerance_limit_returns_true(
    pose1, pose2, position_tolerance, orientation_tolerance, expected
):
    assert expected is MoveItInterface.compare_poses(
        pose1, pose2, position_tolerance, orientation_tolerance
    )


@pytest.mark.parametrize(
    'joints1, joints2, tolerance, expected',
    [
        (
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            0.1,
            True,
        ),
        (
            [515.52, 322.17, 610.70, 663.10, 397.53, 848.02],
            [515.56, 322.17, 610.62, 663.10, 397.58, 848.02],
            0.1,
            True,
        ),
        (
            [818.62, 772.99, 944.91, 654.27, 64.19, 280.57],
            [818.7, 772.99, 944.91, 654.2, 64.19, 280.57],
            0.01,
            False,
        ),
    ],
)
def test_comparing_joints_within_tolerance_limit_returns_true(
    joints1, joints2, tolerance, expected
):
    assert expected is MoveItInterface.compare_joints(
        joints1, joints2, tolerance
    )

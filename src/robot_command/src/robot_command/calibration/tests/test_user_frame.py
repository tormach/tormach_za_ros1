from math import pi

import pytest

from robot_command.calibration import (
    calculate_user_frame_3,
    calculate_user_frame_4,
)
from robot_command.rpl import Pose, RobotProgramError


@pytest.mark.parametrize(
    'waypoints, frame',
    [
        ((Pose(0, 0), Pose(1, 0), Pose(0, 1)), Pose()),
        ((Pose(0, 0), Pose(0, 1), Pose(-1, 0)), Pose(c=pi / 2)),
    ],
)
def test_calculate_user_frame_from_3_waypoints_works(waypoints, frame):
    result = calculate_user_frame_3(*waypoints)

    assert result.x == pytest.approx(frame.x)
    assert result.y == pytest.approx(frame.y)
    assert result.z == pytest.approx(frame.z)
    assert result.a == pytest.approx(frame.a)
    assert result.b == pytest.approx(frame.b)
    assert result.c == pytest.approx(frame.c)


def test_calculate_user_frame_from_3_matching_waypoints_raises_exception():
    with pytest.raises(RobotProgramError):
        calculate_user_frame_3(Pose(), Pose(), Pose())


@pytest.mark.parametrize(
    'waypoints, frame',
    [
        (
            (
                Pose(0, 0),
                Pose(1, 0),
                Pose(0, 1),
                Pose(855.54, 330.03, 466.81, 449.27, 607.54, 447.88),
            ),
            Pose(855.54, 330.03, 466.81),
        ),
        (
            (
                Pose(0, 0),
                Pose(0, 1),
                Pose(-1, 0),
                Pose(824.44, 593.07, 559.37, 490.84, 718.74, 203.55),
            ),
            Pose(824.44, 593.07, 559.37, c=pi / 2),
        ),
    ],
)
def test_calculate_user_frame_from_4_waypoints_works(waypoints, frame):
    result = calculate_user_frame_4(*waypoints)

    assert result.x == pytest.approx(frame.x)
    assert result.y == pytest.approx(frame.y)
    assert result.z == pytest.approx(frame.z)
    assert result.a == pytest.approx(frame.a)
    assert result.b == pytest.approx(frame.b)
    assert result.c == pytest.approx(frame.c)

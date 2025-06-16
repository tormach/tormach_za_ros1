from math import radians

import pytest

from robot_command.calibration import (
    calculate_tool_frame_4,
)
from robot_command.rpl import Pose


@pytest.mark.parametrize(
    'waypoints, frame',
    [
        (
            (
                Pose(
                    x=0.4494231652114486,
                    y=0.10682172819516529,
                    z=0.4880376544066349,
                    a=radians(-160.7862100527609),
                    b=radians(27.64013802043834),
                    c=radians(-129.7191134817827),
                ),
                Pose(
                    x=0.49175805798485874,
                    y=0.08261168226817242,
                    z=0.4719376382890203,
                    a=radians(119.33702063785762),
                    b=radians(27.64045804415013),
                    c=radians(-129.71896452214966),
                ),
                Pose(
                    x=0.4395113285178558,
                    y=0.12240500782225378,
                    z=0.47724279366902647,
                    a=radians(-129.76675473898933),
                    b=radians(27.640485459568975),
                    c=radians(-129.7189391409235),
                ),
                Pose(
                    x=0.476783738491153,
                    y=0.1269640290262479,
                    z=0.49113125541836155,
                    a=radians(-169.3417255323702),
                    b=radians(-21.578433725562537),
                    c=radians(-138.92416726572424),
                ),
            ),
            Pose(0, 0, 0.04),
        ),
    ],
)
def test_calculate_tool_frame_from_4_waypoints_works(waypoints, frame):
    result = calculate_tool_frame_4(*waypoints)

    assert result.x == pytest.approx(frame.x, abs=1e-6)
    assert result.y == pytest.approx(frame.y, abs=1e-6)
    assert result.z == pytest.approx(frame.z, abs=1e-6)
    assert result.a == pytest.approx(frame.a)
    assert result.b == pytest.approx(frame.b)
    assert result.c == pytest.approx(frame.c)

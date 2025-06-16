#!/usr/bin/env python
"""
Test the movel between two goals on a plane parallel to XY plane
Change the velocity scale roughly in the middle of the move
"""
import pytest

from robot_test.helpers import start_program
from robot_test.utils.config_manager_publisher import ConfigManagerPublisher
from robot_test.utils.velocity_transition_handler import (
    VelocityTransitionHandler,
)

import time

MAXVEL_SCALE_PARAMETER = "user_config/maximum_velocity_scale"
WAIT_TIME = 1.0


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        j,
        p,
        pause,
        set_tool_frame,
        change_tool_frame,
        Pose,
    )

    import PyKDL

    set_units("mm", "rad", "s")

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))
    change_tool_frame("flange_frame")

    def main():
        set_units("mm", "rad", "s")
        movej(j[0.0, 0.0, 0.0, 0.0, 1.5708, 0.0], velocity_scale=1.0)
        movej(p[600.0, -300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=1.0)

        pause()
        movej(p[600.0, 300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=0.5)
        pause()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.fixture(scope="module", autouse=True)
def vel_slider():
    """
    Modify parameters in the config manager
    """
    vel_slider = ConfigManagerPublisher()
    return vel_slider


@pytest.fixture(scope="module", autouse=True)
def vel_transition():
    vel_transition = VelocityTransitionHandler()
    transition_time = 0.2
    vel_transition.set_transition_time(transition_time)
    time.sleep(WAIT_TIME)
    return vel_transition


def test_maxvel_scale(launcher, vel_slider):
    vel_slider.publish_update(MAXVEL_SCALE_PARAMETER, "0.25", delay=0)
    time.sleep(WAIT_TIME)

    start_time = time.time()
    assert launcher.cycle_start()
    end_time = time.time()
    execution_time = end_time - start_time

    assert execution_time == pytest.approx(2.30, abs=0.1)

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

import os
import time
from datetime import datetime

UNIFORM_VEL_SCALE_PARAMETER = "user_config/uniform_velocity_scale"
WAIT_TIME = 1.0


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        movel,
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

    VEL = 1000.0  # mm/s

    def main():
        pause()
        movej(j[0.0, 0.0, 0.0, 0.0, 1.5708, 0.0], velocity_scale=0.3)
        movel(p[600.0, -500.0, 450.0, 3.14, 0.0, 0.0], velocity=VEL)

        for i in range(6):
            pause()
            movel(p[600.0, 500.0, 450.0, 3.14, 0.0, 0.0], velocity=VEL)
            pause()
            movel(p[600.0, -500.0, 450.0, 3.14, 0.0, 0.0], velocity=VEL)

        pause()
        movej(j[0.0, 0.0, 0.0, 0.0, 0.5708, 0.0], velocity_scale=0.3)
        pause()
        exit()


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
    return vel_transition


# Get the current date and time in YYYYMMDD_HHMMSS format
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
# Get the home directory
home_directory = os.path.expanduser("~")
# Create the new folder name with the current date and time
folder_name = f"movel_2_pos_jerky_{current_datetime}"
# Get the full directory path
full_directory = os.path.join(home_directory, folder_name)

start_vel_scale = "1.0"
low_vel_scale = "0.5"
later_vel_scale = "1.0"


def test_set_init_position(launcher):
    """Moves robot to the startpoint for movel"""
    assert launcher.cycle_start()


vel_transition_times = [0.2]


@pytest.mark.parametrize("transition_time", vel_transition_times)
def test_movel_sequence(launcher, vel_slider, vel_transition, transition_time):
    # Set transition time for velocity scale change
    vel_transition.set_transition_time(transition_time)
    time.sleep(WAIT_TIME)

    # Set initial velocity scale value with no delay
    vel_slider.publish_update(
        UNIFORM_VEL_SCALE_PARAMETER, start_vel_scale, delay=0
    )

    # Wait for scale to achieve their goal values
    time.sleep(transition_time)

    # Change velocity scale value to low value, wait a bit, then change to high value
    # These are non-blocking calls
    vel_slider.publish_update(
        UNIFORM_VEL_SCALE_PARAMETER, low_vel_scale, delay=1
    )
    vel_slider.publish_update(
        UNIFORM_VEL_SCALE_PARAMETER, later_vel_scale, delay=4
    )

    # Resume the program from paused state, this triggers the HAL sampler to start
    assert launcher.cycle_start()

    time.sleep(WAIT_TIME)
    vel_slider.publish_update(
        UNIFORM_VEL_SCALE_PARAMETER, start_vel_scale, delay=0
    )
    time.sleep(transition_time)
    vel_slider.publish_update(
        UNIFORM_VEL_SCALE_PARAMETER, low_vel_scale, delay=1
    )
    vel_slider.publish_update(
        UNIFORM_VEL_SCALE_PARAMETER, later_vel_scale, delay=4
    )

    assert launcher.cycle_start()
    time.sleep(WAIT_TIME)
    time.sleep(WAIT_TIME)
    time.sleep(WAIT_TIME)


def test_movej_last(launcher):
    assert launcher.cycle_start()
    time.sleep(WAIT_TIME)
    time.sleep(WAIT_TIME)

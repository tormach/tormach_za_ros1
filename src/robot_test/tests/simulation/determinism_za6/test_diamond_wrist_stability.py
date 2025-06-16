#!/usr/bin/env python

# Check if robot arm picks reproducible joint poses
# When moving (movej) between two distant p[] poses

import pytest
import time
import os

from robot_test.helpers import start_program
from robot_test.utils.trajectory_data_saver import TrajectoryDataSaver


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        movel,
        p,
        j,
        pause,
        Pose,
        set_tool_frame,
        change_tool_frame,
        set_user_frame,
        change_user_frame,
    )

    import PyKDL

    set_units("mm", "deg")

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))
    change_tool_frame("flange_frame")

    new_user_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_user_frame("new_user_frame", Pose.from_kdl_frame(new_user_frame))
    change_user_frame("new_user_frame")

    center = p[544.500, 0.000, 121.498, 180.0, 0.0, 0.0]
    bottom = p[200.0, 0.000, 121.498, 180.0, 0.0, 0.0]
    right = p[544.500, -500.000, 121.498, 180.0, 0.0, 0.0]
    top = p[850.0, 0.0, 121.507, 180.000, 0.0, 0.0]
    left = p[544.500, 500.000, 121.498, 180.0, 0.0, 0.0]

    ACCEL = 0.6 * 1000
    VEL = 100

    def main():
        pause()
        movej(j[0.0, 0.0, 0.0, 0.0, 0.1, 0.0])
        movej(center)
        pause()
        movel(bottom, velocity=VEL, accel=ACCEL)
        pause()
        movel(right, velocity=VEL, accel=ACCEL)
        pause()
        movel(top, velocity=VEL, accel=ACCEL)
        pause()
        movel(left, velocity=VEL, accel=ACCEL)
        pause()
        movel(bottom, velocity=VEL, accel=ACCEL)
        pause()
        movel(center, velocity=VEL, accel=ACCEL)


@pytest.fixture(scope="module", autouse=True)
def trajectory_saver():
    test_script_name = os.path.basename(__file__)
    test_script_name_no_extension = os.path.splitext(test_script_name)[0]
    trajectory_saver = TrajectoryDataSaver(
        program_name=test_script_name_no_extension
    )
    yield trajectory_saver
    trajectory_saver.final_cleanup()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


def test_movej_p_sequence(launcher, trajectory_saver):
    assert launcher.cycle_start(), "Cycle start failed."

    trajectory_saver.reset_data()
    trajectory_saver.allow_data_capture = True
    trajectory_saver.append_move_name("movel bottom")
    assert launcher.cycle_start(), "Cycle start failed."
    time.sleep(0.5)
    assert trajectory_saver.check_planning_time()

    trajectory_saver.append_move_name("movel right")
    assert launcher.cycle_start()
    time.sleep(0.5)
    assert trajectory_saver.check_planning_time()

    trajectory_saver.append_move_name("movel top")
    assert launcher.cycle_start()
    time.sleep(0.5)
    assert trajectory_saver.check_planning_time()

    trajectory_saver.append_move_name("movel left")
    assert launcher.cycle_start()
    time.sleep(0.5)
    assert trajectory_saver.check_planning_time()

    trajectory_saver.append_move_name("movel bottom")
    assert launcher.cycle_start()
    time.sleep(0.5)
    assert trajectory_saver.check_planning_time()

    trajectory_saver.append_move_name("movel center")
    assert launcher.cycle_start()
    time.sleep(0.5)
    assert trajectory_saver.check_planning_time()

    trajectory_saver.save_trajectory_points()

    trajectory_saver.reset_data()

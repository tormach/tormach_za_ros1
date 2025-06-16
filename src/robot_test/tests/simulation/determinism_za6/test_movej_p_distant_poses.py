#!/usr/bin/env python

# Check if robot arm picks reproducible joint poses
# When moving (movej) between two distant p[] poses

import pytest
import time

from robot_test.helpers import start_program
from robot_test.utils.trajectory_data_saver import TrajectoryDataSaver


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        p,
        j,
        pause,
        set_tool_frame,
        change_tool_frame,
        Pose,
    )

    import PyKDL

    set_units("mm", "deg", "s")

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))
    change_tool_frame("flange_frame")

    rando_1 = p[238.000, 501.000, 997.000, 125.606, -89.916, -114.700]
    rando_2 = p[-205.125, 41.828, 1011.476, 126.040, -89.917, -115.134]

    def main():
        movej(j[16.03, -3.44, -3.32, -59.61, 99.73, 83.14], velocity_scale=0.2)

        while True:
            pause()
            movej(rando_1, velocity_scale=0.2)
            pause()
            movej(rando_2, velocity_scale=0.2)


@pytest.fixture(scope="module", autouse=True)
def trajectory_saver():
    trajectory_saver = TrajectoryDataSaver(time_limit=0.4)
    yield trajectory_saver
    trajectory_saver.final_cleanup()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.fixture(scope='module', autouse=True)
def pose_data():
    poses = [{} for _ in range(2)]
    poses[0] = [
        -2.1653694862088417,
        -1.0842035458003647,
        -1.0562186229130655,
        -0.87175990755003,
        1.9626274936282528,
        -0.4267479731170343,
    ]

    poses[1] = [
        -0.6340559737160022,
        -1.043728573537626,
        0.21144484322499693,
        -2.170126708822244,
        2.046235736007208,
        0.588229279326576,
    ]
    return poses


@pytest.mark.parametrize('run', range(1))
def test_movej_p_sequence(run, launcher, trajectory_saver, pose_data):
    trajectory_saver.allow_data_capture = True
    assert launcher.cycle_start(), f"run {run}: Cycle start failed."
    time.sleep(3.0)
    assert (
        trajectory_saver.check_planning_time()
    ), f"run {run}, point 1 goal: Planning time is too long."
    assert trajectory_saver.joints_position() == pytest.approx(
        pose_data[0], abs=0.01
    ), f"run {run}, point 1 goal: Joints pose is not correct."
    trajectory_saver.reset_data()

    assert launcher.cycle_start(), f"run {run}: Cycle start failed."
    time.sleep(3.0)
    assert (
        trajectory_saver.check_planning_time()
    ), f"run {run}, point 2 goal: Planning time is too long."
    assert trajectory_saver.joints_position() == pytest.approx(
        pose_data[1], abs=0.01
    ), f"run {run}, point 2 goal: Joints pose is not correct."
    trajectory_saver.reset_data()

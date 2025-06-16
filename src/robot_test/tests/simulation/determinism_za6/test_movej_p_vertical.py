#!/usr/bin/env python

# Check if movej(p[]) between two close cartesian goals is working correctly
# Pairs of goals where each pair lis in a different arm configuration are considered

import pytest

from robot_test.helpers import start_program
from robot_test.utils.trajectory_data_saver import TrajectoryDataSaver
import math
import os


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
        NUT,
        FUT,
        NUB,
        FUB,
    )

    import PyKDL

    set_units("mm", "rad", "s")

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))
    change_tool_frame("flange_frame")

    x1 = 408.6
    y1 = 16.5
    z1 = 926.8
    a1 = 2.99
    b1 = -1.02
    c1 = -1.25

    x2 = 408.6
    y2 = 16.5
    z2 = 1100.65
    a2 = 0.1425
    b2 = -1.02
    c2 = 1.64

    def main():
        vel = 1.0
        # start with a known joint configuration (important for the first test)
        movej(j[0.28, -0.06, -0.058, -1.04, 1.74, 1.45], velocity_scale=vel)

        # test moving to the closest configurations
        pause()
        movej(p[x1, y1, z1, a1, b1, c1], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2], velocity_scale=vel)

        # test configuration only
        pause()
        movej(p[x1, y1, z1, a1, b1, c1, NUT], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, NUT], velocity_scale=vel)

        pause()
        movej(p[x1, y1, z1, a1, b1, c1, FUT], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, FUT], velocity_scale=vel)

        pause()
        movej(p[x1, y1, z1, a1, b1, c1, NUB], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, NUB], velocity_scale=vel)

        pause()
        movej(p[x1, y1, z1, a1, b1, c1, FUB], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, FUB], velocity_scale=vel)

        # test configuration and reachable revolution counts
        pause()
        movej(p[x1, y1, z1, a1, b1, c1, NUT, 0], velocity_scale=vel)
        pause()
        movej(p[x1, y1, z1, a1, b1, c1, NUT, -1], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, NUT, 0], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, NUT, -1], velocity_scale=vel)

        pause()
        movej(p[x1, y1, z1, a1, b1, c1, FUT, 0], velocity_scale=vel)
        pause()
        movej(p[x1, y1, z1, a1, b1, c1, FUT, 1], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, FUT, 0], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, FUT, 1], velocity_scale=vel)

        pause()
        movej(p[x1, y1, z1, a1, b1, c1, NUB, 0], velocity_scale=vel)
        pause()
        movej(p[x1, y1, z1, a1, b1, c1, NUB, 1], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, NUB, 0], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, NUB, 1], velocity_scale=vel)

        pause()
        movej(p[x1, y1, z1, a1, b1, c1, FUB, 0], velocity_scale=vel)
        pause()
        movej(p[x1, y1, z1, a1, b1, c1, FUB, -1], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, FUB, 0], velocity_scale=vel)
        pause()
        movej(p[x2, y2, z2, a2, b2, c2, FUB, -1], velocity_scale=vel)

        exit()


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


@pytest.fixture(scope='module', autouse=True)
def pose_data():
    # Define joint values of two Cartesian poses. Each pose has 4 reachable configurations.
    poses = [{} for _ in range(2)]
    poses[0]["NUT"] = [0.2874, -0.0582, -0.0624, -1.0385, 1.7560, 1.4486]
    poses[0]["FUT"] = [0.2898, -0.0585, -0.0579, 2.1037, -1.7560, -1.6881]
    poses[0]["NUB"] = [-2.8573, -1.3111, -0.1673, 1.3758, 2.0991, -0.1983]
    poses[0]["FUB"] = [-2.8582, -1.3107, -0.1724, -1.7621, -2.1001, 2.9486]

    poses[1]["NUT"] = [0.2921, -0.0474, -0.2011, -2.1125, 1.4897, 1.2421]
    poses[1]["FUT"] = [0.2895, -0.0477, -0.1966, 1.0292, -1.4897, -1.894]
    poses[1]["NUB"] = [-2.8557, -1.1899, -0.3076, 1.5654, 1.02419, -0.1726]
    poses[1]["FUB"] = [-2.8557, -1.1895, -0.3129, -1.5790, -1.0242, 2.9746]

    # define the optional reachable revolution count values for each pose
    rev_counts = [{} for _ in range(2)]
    rev_counts[0]["NUT"] = -1
    rev_counts[0]["FUT"] = 1
    rev_counts[0]["NUB"] = 1
    rev_counts[0]["FUB"] = -1

    rev_counts[1]["NUT"] = -1
    rev_counts[1]["FUT"] = 1
    rev_counts[1]["NUB"] = 1
    rev_counts[1]["FUB"] = -1

    def create_poses_rev(poses, rev_counts):
        poses_rev = [{} for _ in range(2)]
        for i in range(2):
            for conf in ["NUT", "FUT", "NUB", "FUB"]:
                poses_rev[i][conf] = poses[i][
                    conf
                ].copy()  # Copy the original pose
                rev_count = rev_counts[i][conf]
                poses_rev[i][conf][-1] += 2 * math.pi * rev_count

        return poses_rev

    poses_rev = create_poses_rev(poses, rev_counts)

    return poses, poses_rev


def test_movej_p_no_config(launcher, trajectory_saver, pose_data):
    poses, poses_rev = pose_data
    # go to pose_1 without specified config

    trajectory_saver.reset_data()
    trajectory_saver.allow_data_capture = True
    trajectory_saver.append_move_name("movel bottom")
    assert launcher.cycle_start()
    assert (
        trajectory_saver.check_planning_time()
    ), "Planing time failed for pose_1 NUT"
    assert trajectory_saver.joints_position() == pytest.approx(
        poses[0]["NUT"], abs=0.01
    )
    trajectory_saver.reset_data()

    # go to pose_2 without specified config
    assert launcher.cycle_start()
    assert (
        trajectory_saver.check_planning_time()
    ), "Planing time failed for pose_2 NUT"
    assert trajectory_saver.joints_position() == pytest.approx(
        poses[1]["NUT"], abs=0.01
    )
    trajectory_saver.reset_data()


@pytest.mark.parametrize("conf", ["NUT", "FUT", "NUB", "FUB"])
def test_movej_p_config(launcher, trajectory_saver, conf, pose_data):
    poses, poses_rev = pose_data
    # go to pose_1 with selected config and IMPLICIT revolution count 0
    assert launcher.cycle_start()
    assert (
        trajectory_saver.check_planning_time()
    ), f"Planing time failed for pose_1, {conf}"
    assert trajectory_saver.joints_position() == pytest.approx(
        poses[0][conf], abs=0.01
    )
    trajectory_saver.reset_data()

    # go to pose_2 with selected config and IMPLICIT revolution count 0
    assert launcher.cycle_start()
    assert (
        trajectory_saver.check_planning_time()
    ), f"Planing time failed for pose_2, {conf}"
    assert trajectory_saver.joints_position() == pytest.approx(
        poses[1][conf], abs=0.01
    )
    trajectory_saver.reset_data()

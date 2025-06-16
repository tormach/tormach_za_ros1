#!/usr/bin/env python

# Check if robot arm picks the closes arm configuration and revolution count
# with respect to the current arm pose.

# The arm traverses across the points that go through the J6 range
# of -360 deg to + 360 across 4 different sequences
# Each sequence draws a half of the letter "U" in the Cartesian space

import pytest

from robot_test.helpers import start_program

from robot_test.utils.arm_config_handler import ArmConfigHandler

from movej_ik_server_msgs.msg import ArmConfigs


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

    set_units("mm", "rad", "s")

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))
    change_tool_frame("flange_frame")

    def main():
        movej(j[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], velocity_scale=0.3)
        movej(j[0.0, 1.0, 0.0, 0.0, -1.0, 0.0], velocity_scale=0.3)
        movej(j[0.0, 1.0, 0.0, 0.0, -1.0, 3.1415], velocity_scale=0.3)

        x_dist = 500.0  # do not change

        points_negative = [
            p[x_dist, -300.0, 350.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -300.0, 550.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -300.0, 750.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -300.0, 950.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -300.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -200.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -150.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -100.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -50.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, -10.0, 1150.0, 2.5601, 1.5700, 2.5611],
        ]

        points_positive = [
            p[x_dist, 300.0, 350.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 300.0, 550.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 300.0, 750.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 300.0, 950.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 300.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 200.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 150.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 100.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 50.0, 1150.0, 2.5601, 1.5700, 2.5611],
            p[x_dist, 10.0, 1150.0, 2.5601, 1.5700, 2.5611],
        ]

        vel_scale = 0.7

        # Test range 180 to 360 deg
        for point in points_negative:
            pause()
            movej(point, velocity_scale=vel_scale)

        movej(j[0.0, 1.0, 0.0, 0.0, -1.0, 3.1415], velocity_scale=0.3)

        # Test range 0 to 180 deg
        for point in points_positive:
            pause()
            movej(point, velocity_scale=vel_scale)

        # movej(j[0.0, 57.296, 0.0, 0.0, -57.296, -180.0], velocity_scale=vel_scale)
        movej(j[0.0, 1.0, 0.0, 0.0, -1.0, -3.1415], velocity_scale=0.3)

        # Test range -180 to 0 deg
        for point in points_negative:
            pause()
            movej(point, velocity_scale=vel_scale)

        # movej(j[0.0, 57.296, 0.0, 0.0, -57.296, -180.0], velocity_scale=vel_scale)
        movej(j[0.0, 1.0, 0.0, 0.0, -1.0, -3.1415], velocity_scale=0.3)

        # Test range -360 to -180 deg
        for point in points_positive:
            pause()
            movej(point, velocity_scale=vel_scale)


@pytest.fixture(scope="module", autouse=True)
def arm_config_handler():
    handler = ArmConfigHandler()
    yield handler


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


def append_string_to_file(filename, text):
    with open(filename, 'a') as f:
        f.write(text + '\n')


test_numbers = range(10)

p180_p360_configs = [
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
]

p180_p360_rev_counts = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
p180_p360_data = list(
    zip(p180_p360_configs, p180_p360_rev_counts, test_numbers)
)

p0_p180_configs = [
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
]

p0_p180_rev_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, -1]
p0_p180_data = list(zip(p0_p180_configs, p0_p180_rev_counts, test_numbers))

n180_p0_configs = [
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
]
n180_p0_rev_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, -1]
n180_p0_data = list(zip(n180_p0_configs, n180_p0_rev_counts, test_numbers))

n360_n180_configs = [
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
    ArmConfigs.FUT,
]

n360_n180_rev_counts = [-1, -1, -1, -1, -1, -1, -1, -1, -1, 0]
n360_n180_data = list(
    zip(n360_n180_configs, n360_n180_rev_counts, test_numbers)
)


@pytest.mark.parametrize(
    "expected_arm_config,expected_rev,test_number", p180_p360_data
)
def test_rev_p180_p360_range(
    launcher, arm_config_handler, expected_arm_config, expected_rev, test_number
):
    assert launcher.cycle_start()
    arm_config, count = arm_config_handler.get_config()
    assert (
        arm_config == expected_arm_config
    ), f"Test {test_number} failed: Expected arm_config"
    assert (
        count == expected_rev
    ), f"Test {test_number} failed: on Expected rev_count"


@pytest.mark.parametrize(
    "expected_arm_config,expected_rev,test_number", p0_p180_data
)
# def test_p0_p180_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_p0_p180_range(
    launcher, arm_config_handler, expected_arm_config, expected_rev, test_number
):
    assert launcher.cycle_start()
    arm_config, count = arm_config_handler.get_config()
    assert (
        arm_config == expected_arm_config
    ), f"Test {test_number} failed: Expected arm_config"
    assert (
        count == expected_rev
    ), f"Test {test_number} failed: on Expected rev_count"


@pytest.mark.parametrize(
    "expected_arm_config,expected_rev,test_number", n180_p0_data
)
# def test_n180_p0_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_n180_p0_range(
    launcher, arm_config_handler, expected_arm_config, expected_rev, test_number
):
    assert launcher.cycle_start()
    arm_config, count = arm_config_handler.get_config()
    assert (
        arm_config == expected_arm_config
    ), f"Test {test_number} failed: Expected arm_config"
    assert (
        count == expected_rev
    ), f"Test {test_number} failed: on Expected rev_count"


@pytest.mark.parametrize(
    "expected_arm_config,expected_rev,test_number", n360_n180_data
)
# def test_n360_n180_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_n360_n180_range(
    launcher, arm_config_handler, expected_arm_config, expected_rev, test_number
):
    assert launcher.cycle_start()
    arm_config, count = arm_config_handler.get_config()
    assert (
        arm_config == expected_arm_config
    ), f"Test {test_number} failed: Expected arm_config"
    assert (
        count == expected_rev
    ), f"Test {test_number} failed: on Expected rev_count"

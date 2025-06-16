#!/usr/bin/env python

# These are not real tests but data collection snippets
# Collect data for testing arm configs with revolution count

import pytest
from robot_test.helpers import start_program
from ..utils.arm_config_handler import ArmConfigHandler


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

        # movej(j[0.0, 57.296, 0.0, 0.0, -57.296, 180.0], velocity_scale=vel_scale)
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


robot_configs = [
    "FUB",
    "FUB",
    "FUB",
    "FUT",
    "NUT",
    "NUT",
    "NUT",
    "NUT",
    "NUT",
    "NUB",
    "NUT",
    "NUT",
]
rev_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
test_numbers = range(len(robot_configs))

test_numbers = range(10)


@pytest.mark.parametrize("test_number", test_numbers)
# def test_rev_p180_p360_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_rev_p180_p360_range(launcher, arm_config_handler, test_number):
    assert launcher.cycle_start()
    config_string, count = arm_config_handler.get_config()
    append_string_to_file("range_p180_to_p360.txt", config_string)
    append_string_to_file("range_p180_to_p360_rev.txt", str(count))


@pytest.mark.parametrize("test_number", test_numbers)
# def test_p0_p180_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_p0_p180_range(launcher, arm_config_handler, test_number):
    assert launcher.cycle_start()
    config_string, count = arm_config_handler.get_config()
    append_string_to_file("range_p0_to_p180.txt", config_string)
    append_string_to_file("range_p0_to_p180_rev.txt", str(count))


@pytest.mark.parametrize("test_number", test_numbers)
# def test_n180_p0_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_n180_p0_range(launcher, arm_config_handler, test_number):
    assert launcher.cycle_start()
    config_string, count = arm_config_handler.get_config()
    append_string_to_file("range_n180_to_p0.txt", config_string)
    append_string_to_file("range_n180_to_p0_rev.txt", str(count))


@pytest.mark.parametrize("test_number", test_numbers)
# def test_n360_n180_range(launcher, arm_config_handler, config, rev_count, test_number):
def test_n360_n180_range(launcher, arm_config_handler, test_number):
    assert launcher.cycle_start()
    config_string, count = arm_config_handler.get_config()
    append_string_to_file("range_n360_to_n180.txt", config_string)
    append_string_to_file("range_n360_to_n180_rev.txt", str(count))

#!/usr/bin/env python

# Check if arm configurations are correctly assigned
# when arm is in different joint poses

# This test checks if ROS1 service used to retrieve arm configurations
# for p[] waypoints created in teaching mode is working correctly

import pytest
import itertools

from robot_test.helpers import start_program

from robot_test.utils.arm_config_handler import ArmConfigHandler

from movej_ik_server_msgs.msg import ArmConfigs


def program():
    from robot_command.rpl import (  # noqa: F401
        set_units,
        movej,
        j,
        pause,
    )

    set_units("mm", "rad", "s")

    def main():
        pause()
        movej(j[0.0, -0.80, 0.0, 0.0, 0.001, 0.0], velocity_scale=0.3)  # NUT
        pause()
        movej(j[0.0, -0.80, 0.0, 0.0, -0.001, 0.0], velocity_scale=0.3)  # FUT
        pause()
        movej(j[0.0, -0.80, 0.0, 0.0, 0.8, 0.0], velocity_scale=0.3)  # NUT
        pause()
        movej(j[0.0, 0.30, -1.50, 0.0, 0.8, 0.0], velocity_scale=0.3)  # NDT
        pause()
        movej(j[0.0, -1.30, 0.0, 0.0, 0.8, 0.0], velocity_scale=0.3)  # NUB
        pause()
        movej(j[0.0, -0.40, -1.50, 0.0, 0.8, 0.0], velocity_scale=0.3)  # NDB
        pause()
        movej(j[0.0, -0.40, 0.0, 0.0, -1.8, 0.0], velocity_scale=0.3)  # FUT
        pause()
        movej(j[0.0, 0.30, -1.50, 0.0, -1.8, 0.0], velocity_scale=0.3)  # FDT
        pause()
        movej(j[0.0, -0.80, 0.0, 0.0, -1.8, 0.0], velocity_scale=0.3)  # FUB
        pause()
        movej(j[0.0, -0.40, -1.50, 0.0, -1.8, 0.0], velocity_scale=0.3)  # FDB
        pause()

        exit()


@pytest.fixture(scope="module", autouse=True)
def arm_config_handler():
    handler = ArmConfigHandler()
    yield handler


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.fixture(scope='function')
def test_counter():
    return itertools.count()


expected_arm_configs = [
    ArmConfigs.NUT,
    ArmConfigs.FUT,
    ArmConfigs.NUT,
    ArmConfigs.NDT,
    ArmConfigs.NUB,
    ArmConfigs.NDB,
    ArmConfigs.FUT,
    ArmConfigs.FDT,
    ArmConfigs.FUB,
    ArmConfigs.FDB,
]

rev_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
test_numbers = range(len(expected_arm_configs))

test_data = list(zip(expected_arm_configs, rev_counts, test_numbers))


@pytest.mark.parametrize(
    "expected_config,expected_rev_count,test_number", test_data
)
def test_configs(
    launcher,
    arm_config_handler,
    expected_config,
    expected_rev_count,
    test_number,
):
    assert launcher.cycle_start()
    arm_config, rev_count = arm_config_handler.get_config()
    assert (
        arm_config == expected_config
    ), f"Test {test_number} failed: Expected config: {expected_config}, got {arm_config}"
    assert (
        rev_count == expected_rev_count
    ), f"Test {test_number} failed: Expected rev_count: {rev_count}, got {rev_count}"

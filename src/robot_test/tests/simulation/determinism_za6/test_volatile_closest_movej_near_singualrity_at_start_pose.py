#!/usr/bin/env python

# Test sending service request to movej_closest_ik_service
# without acually moving the robot
# IF start pose wrist singularity safety check is turn off,
# this test would give non-deteministic movej goal joint configuration
# result for a given start pose

import pytest

from robot_test.helpers import start_program

from robot_test.utils.ik_client import IKClient

from movej_ik_server_msgs.msg import ArmConfigs


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        j,
        pause,
    )

    set_units("mm", "rad", "s")

    def main():
        """
        Move robot to a specified pose that will be used a starting point for
        ROS service request done by the ik_client inside the test functions
        Note that for node-level testing purposes, the robot is not actually moved
        to the tested goal poses specified in the requests.
        """
        # pose near wrist singularity known to fail non-deterministically:
        # BioIK solution does not always converge from the start OPW seed
        # this is handled with safety checks for the start pose
        movej(j[0.0, -0.6, 0.75, 0.0, 0.006, 0.0], velocity_scale=0.3)
        pause()


@pytest.fixture(scope="module", autouse=True)
def ik_client():
    client = IKClient()
    yield client


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


# this test is expected to fail if the safety check for the start pose is turned off
def test_movej_closest_pose(launcher, ik_client):
    expected_joints = [0.001, 0.4665, 0.2744, -0.010, 0.1081, 0.012]
    response = ik_client.send_closest_service_request(
        [0.640, 0.0, 0.510, 3.1416, -0.7219, 0.0]
    )

    assert response.success is True
    assert response.arm_config == ArmConfigs.NUT
    assert response.rev_count == 0
    assert response.joint_values == pytest.approx(expected_joints, abs=0.001)

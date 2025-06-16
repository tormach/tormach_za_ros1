#!/usr/bin/env python

# Test sending service request to movej_closest_ik_service
# without acually moving the robot

import pytest

from robot_test.helpers import start_program

from robot_test.utils.ik_client import IKClient

from movej_ik_server_msgs.msg import IKSolverWarning


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

        movej(j[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], velocity_scale=0.3)  # FDB
        pause()


@pytest.fixture(scope="module", autouse=True)
def ik_client():
    client = IKClient()
    yield client


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


def test_small_j5_value_at_goal_pose(launcher, ik_client):
    response = ik_client.send_closest_service_request(
        [0.532312, 0.0, 0.525966, 3.1416, -0.6908, 0.0]
    )

    assert response.success
    assert len(response.error_codes) == 0
    assert len(response.warning_codes) == 1
    assert (
        response.warning_codes[0]
        == IKSolverWarning.START_POSE_WRIST_NEAR_SINGULARITY
    )

#!/usr/bin/env python

# Test sending service request to movej_closest_ik_service
# without acually moving the robot

import pytest

from robot_test.helpers import start_program

from robot_test.utils.ik_client import IKClient

from movej_ik_server_msgs.msg import IKSolverError


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

        pause()
        movej(j[0.0, -0.81, 0.18, 0.0, 0.10, 0.0], velocity_scale=0.3)
        pause()


@pytest.fixture(scope="module", autouse=True)
def ik_client():
    client = IKClient()
    yield client


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


def test_move_robot_to_startup_pose(launcher, ik_client):
    assert launcher.cycle_start()


def test_fatal_goal_ik_solutions_mismatch(launcher, ik_client):
    response = ik_client.send_closest_service_request(
        [0.304745, 0.0, 0.778364, 3.1416, -1.4148, 0.0]
    )

    assert not response.success
    assert len(response.error_codes) == 2

    assert response.error_codes[0] == IKSolverError.WRIST_NEAR_SINGULARITY

    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 0


def test_fatal_goal_wrist_singularity_error(launcher, ik_client):
    response = ik_client.send_closest_service_request(
        [0.304274, 0.0, 0.775584, 3.1416, -1.3908, 0.0]
    )

    assert not response.success
    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.WRIST_NEAR_SINGULARITY
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 0

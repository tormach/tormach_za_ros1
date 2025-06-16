#!/usr/bin/env python

# Test sending service request to movej_closest_ik_service
# without acually moving the robot
# TODO: check error & warning codes more thoroughly

import pytest

from robot_test.helpers import start_program

from robot_test.utils.ik_client import IKClient

from movej_ik_server_msgs.msg import ArmConfigs, IKSolverWarning, IKSolverError


def program():
    from robot_command.rpl import (  # noqa: F401
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
        when we send the service requests in the test functions
        """
        movej(j[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], velocity_scale=0.3)
        pause()


@pytest.fixture(scope="module", autouse=True)
def ik_client():
    client = IKClient()
    yield client


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


excessive_z_position = 10.0


def test_movej_closest_pose_analitical_failure(launcher, ik_client):
    response = ik_client.send_closest_service_request(
        [0.4086, 0.0165, excessive_z_position, 2.99, -1.02, -1.25]
    )

    assert not response.success
    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.NO_ANALYTICAL_SOLUTION
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 1
    assert (
        response.warning_codes[0]
        == IKSolverWarning.START_POSE_WRIST_NEAR_SINGULARITY
    )


def test_movej_closest_pose_force_config_analitical_failure(
    launcher, ik_client
):
    expected_arm_config = ArmConfigs.FUT
    response = ik_client.send_closest_service_request(
        [0.4086, 0.0165, excessive_z_position, 2.99, -1.02, -1.25],
        expected_arm_config,
    )

    assert not response.success
    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.NO_ANALYTICAL_SOLUTION
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 1
    assert (
        response.warning_codes[0]
        == IKSolverWarning.START_POSE_WRIST_NEAR_SINGULARITY
    )


def test_movej_user_analytical_failure(launcher, ik_client):
    expected_arm_config = ArmConfigs.NUB
    expected_rev_count = 0

    response = ik_client.send_user_service_request(
        [0.4086, 0.0165, excessive_z_position, 2.99, -1.02, -1.25],
        expected_arm_config,
        expected_rev_count,
    )

    assert not response.success
    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.NO_ANALYTICAL_SOLUTION
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 0

#!/usr/bin/env python

# Test sending service request to movej_closest_ik_service
# without acually moving the robot

import pytest

from robot_test.helpers import start_program

from robot_test.utils.ik_client import IKClient

from movej_ik_server_msgs.msg import ArmConfigs, IKSolverWarning


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
        to the tested goal poses specified in the requests.
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


def test_movej_closest_pose(launcher, ik_client):
    response = ik_client.send_closest_service_request(
        [0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25]
    )

    assert response.success
    assert len(response.warning_codes) == 1
    assert (
        response.warning_codes[0]
        == IKSolverWarning.START_POSE_WRIST_NEAR_SINGULARITY
    )
    assert response.arm_config == ArmConfigs.NUT
    assert response.rev_count == 0


def test_movej_closest_pose_2(launcher, ik_client):
    expected_joints = [0.00177, 0.4665, 0.2744, -0.0108, 0.1081, 0.01208]
    response = ik_client.send_closest_service_request(
        [0.640, 0.0, 0.510, 3.1416, -0.7219, 0.0]
    )

    assert response.success
    assert response.arm_config == ArmConfigs.NUT
    assert response.rev_count == 0
    assert response.joint_values == pytest.approx(expected_joints, abs=0.001)


def test_movej_closest_pose_force_config(launcher, ik_client):
    expected_arm_config = ArmConfigs.FUT
    expected_joints = [0.2886, -0.0585, -0.0601, 2.1037, -1.7560, -1.6905]

    response = ik_client.send_closest_service_request(
        [0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25], expected_arm_config
    )

    assert response.success
    assert len(response.error_codes) == 0
    assert len(response.warning_codes) == 1
    assert (
        response.warning_codes[0]
        == IKSolverWarning.START_POSE_WRIST_NEAR_SINGULARITY
    )
    assert response.arm_config == expected_arm_config
    assert response.rev_count == 0
    assert response.joint_values == pytest.approx(expected_joints, abs=0.001)

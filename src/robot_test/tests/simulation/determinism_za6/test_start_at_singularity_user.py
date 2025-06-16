#!/usr/bin/env python

# Test sending service request to movej_closest_ik_service
# without acually moving the robot

import pytest
import math

from robot_test.helpers import start_program

from robot_test.utils.ik_client import IKClient

from movej_ik_server_msgs.msg import ArmConfigs, IKSolverWarning, IKSolverError


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


def test_movej_closest_pose_force_config(launcher, ik_client):
    expected_arm_config = ArmConfigs.FUT
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


def test_movej_user_pose(launcher, ik_client):
    expected_arm_config = ArmConfigs.NUB
    expected_rev_count = 0

    response = ik_client.send_user_service_request(
        [0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        expected_arm_config,
        expected_rev_count,
    )

    assert response.success
    assert len(response.error_codes) == 0
    assert len(response.warning_codes) == 0


def test_failing_movej_user_invalid_config_candidates(launcher, ik_client):
    bad_rev_count = 2

    response = ik_client.send_user_service_request(
        goal_pose=[0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        arm_config=ArmConfigs.NUB,
        rev_count=bad_rev_count,
    )

    assert not response.success
    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.INVALID_CONFIG_CANDIDATES
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 0


def test_movej_user_reachable_rev_count_1(launcher, ik_client):
    response = ik_client.send_user_service_request(
        goal_pose=[0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        arm_config=ArmConfigs.NUB,
        rev_count=1,
    )
    expected_joints = [-2.8573, -1.3111, -0.1674, 1.3758, 2.0991, 6.0848]
    assert response.joint_values == pytest.approx(expected_joints, abs=0.001)
    assert response.success is True
    assert len(response.error_codes) == 0
    assert len(response.warning_codes) == 0


def test_movej_user_reachable_rev_count_0(launcher, ik_client):
    response = ik_client.send_user_service_request(
        goal_pose=[0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        arm_config=ArmConfigs.NUB,
        rev_count=0,
    )
    expected_joints = [
        -2.8573,
        -1.3111,
        -0.1674,
        1.3758,
        2.0991,
        6.0848 - 2 * math.pi,
    ]
    assert response.joint_values == pytest.approx(expected_joints, abs=0.001)
    assert response.success
    assert len(response.error_codes) == 0
    assert len(response.warning_codes) == 0


def test_failing_movej_user_unreachable_rev_count(launcher, ik_client):
    unreachable_rev_count = -1  # valid range, but unreachable for tested pose

    response = ik_client.send_user_service_request(
        goal_pose=[0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        arm_config=ArmConfigs.NUB,
        rev_count=unreachable_rev_count,
    )

    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.UNREACHABLE_REV_COUNT
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 0


ground_truth_joints = [
    [0.2874, -0.0581, -0.0624, -1.0385, 1.7560, 1.4485],
    [0.2899, -0.05850, -0.0580, 2.1037, -1.7560, -1.6882],
    [-2.8573, -1.3111, -0.1674, 1.3758, 2.0991, -0.1983],
    [-2.8583, -1.3108, -0.1725, -1.7621, -2.1001, 2.9486],
]
ground_truth_configs = [
    ArmConfigs.NUT,
    ArmConfigs.FUT,
    ArmConfigs.NUB,
    ArmConfigs.FUB,
]
expected_input = zip(ground_truth_configs, ground_truth_joints)


@pytest.mark.parametrize("expected_arm_config,expected_joints", expected_input)
def test_movej_user_configs_within_joint_limits(
    launcher, ik_client, expected_arm_config, expected_joints
):
    response = ik_client.send_user_service_request(
        goal_pose=[0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        arm_config=expected_arm_config,
        rev_count=0,
    )

    assert response.success is True
    assert response.joint_values == pytest.approx(expected_joints, abs=0.001)
    assert len(response.error_codes) == 0
    assert len(response.warning_codes) == 0


@pytest.mark.parametrize(
    "unreachable_arm_config",
    [ArmConfigs.NDT, ArmConfigs.FDT, ArmConfigs.NDB, ArmConfigs.FDB],
)
def test_failing_movej_configs_outside_joint_limits(
    launcher, ik_client, unreachable_arm_config
):
    response = ik_client.send_user_service_request(
        goal_pose=[0.4086, 0.0165, 0.9268, 2.99, -1.02, -1.25],
        arm_config=unreachable_arm_config,
        rev_count=0,
    )

    assert response.success is not True
    assert len(response.error_codes) == 2
    assert response.error_codes[0] == IKSolverError.NO_NUMERICAL_SOLUTION
    assert response.error_codes[1] == IKSolverError.GOAL_POSE_FAILURE
    assert len(response.warning_codes) == 0

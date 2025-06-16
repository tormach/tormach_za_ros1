#!/usr/bin/env python

# Check if ROS1 /movej_user_ik_service detects when a tool change
# causes a change in the arm configuration. Consider:
#   - no tool change with respect to the cached tool_frame for p[] goal
#   - insignifican tool_frame change (no arm configuration change)
#   - significant tool_frame change (expected arm configuration change)

# This service would be normally called from _create_request() function
# in the moveit_interface.py module, and would use an expanded p[] pose
# This service could be also used to check validity/rechability
# of the p[] goals after a tool change, and before starting the program

# Note that the current state of the robot is not relevant for this test
# We only care about the current tool_frame and the goal pose
# goal poses are now hard-coded in the test fixtures. They would be normally
# stored in the program file or in the database

import rospy

import geometry_msgs.msg

from movej_ik_server_msgs.srv import (
    MovejUserIKService,
    MovejUserIKServiceRequest,
)

from movej_ik_server_msgs.msg import ArmConfigs

import pytest

from robot_test.helpers import start_program
from robot_test.utils.arm_config_handler import ArmConfigHandler


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

    set_units("mm", "rad", "second")

    # Initalize tool frames
    short_offset_frame = PyKDL.Frame(
        PyKDL.Rotation.RotY(-1.508), PyKDL.Vector(-100.0, 0.0, 0.0)
    )
    set_tool_frame(
        "short_offset_frame", Pose.from_kdl_frame(short_offset_frame)
    )

    similar_short_offset_frame = PyKDL.Frame(
        PyKDL.Rotation.RotY(-1.508), PyKDL.Vector(-110.0, 0.0, 0.0)
    )
    set_tool_frame(
        "similar_short_offset_frame",
        Pose.from_kdl_frame(similar_short_offset_frame),
    )

    long_offset_frame = PyKDL.Frame(
        PyKDL.Rotation.RotY(-1.508), PyKDL.Vector(-300.0, 0.0, 0.0)
    )
    set_tool_frame("long_offset_frame", Pose.from_kdl_frame(long_offset_frame))

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))

    def main():
        pause()
        # Note the value of J5 = -0.1, to avoid starting from wrist singularity
        movej(j[0.0, 0.0, 0.0, 0.0, -0.1, 0.0], velocity_scale=1.0)

        change_tool_frame("short_offset_frame")
        z_height = 700.0
        movej(p[600.0, 0.0, z_height, 3.14, 0.0, 0.0], velocity_scale=1.0)

        pause()
        change_tool_frame("similar_short_offset_frame")
        movej(p[600.0, 0.0, z_height, 3.14, 0.0, 0.0], velocity_scale=1.0)

        pause()
        change_tool_frame("long_offset_frame")
        movej(p[600.0, 0.0, z_height, 3.14, 0.0, 0.0], velocity_scale=1.0)

        pause()
        exit()


@pytest.fixture(scope="module", autouse=True)
def arm_config_handler():
    handler = ArmConfigHandler()
    yield handler


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.fixture(scope="module", autouse=True)
def move_ik_service():
    move_ik_service = rospy.ServiceProxy(
        '/movej_user_ik_service', MovejUserIKService
    )
    move_ik_service.wait_for_service()
    return move_ik_service


@pytest.fixture(scope="module", autouse=True)
def poses():
    # endeffector pose for given goal pose p[] when short tool is attached
    # this is the original pose that has the same cached joints, cached arm configuration
    pose_1 = geometry_msgs.msg.Pose()
    pose_1.position.x = 0.6062755063315789
    pose_1.position.y = 0.00015895137315121964
    pose_1.position.z = 0.7998027692739199
    pose_1.orientation.x = 0.7289562364724991
    pose_1.orientation.y = 0.000545133456572109
    pose_1.orientation.z = 0.6845598375391445
    pose_1.orientation.w = 0.0005804875061127526

    # endeffector pose for given goal pose p[] when similar short tool is attached
    # this pose invalidates cached joints, but keeps cached arm configuration
    pose_2 = geometry_msgs.msg.Pose()
    pose_2.position.x = 0.6069030569647368
    pose_2.position.y = 0.0001748465104663416
    pose_2.position.z = 0.8097830462013119
    pose_2.orientation.x = 0.7289562364724991
    pose_2.orientation.y = 0.000545133456572109
    pose_2.orientation.z = 0.6845598375391445
    pose_2.orientation.w = 0.0005804875061127526

    # endeffector pose for given goal pose p[] when long tool is attached
    # this pose invalidates both cached joints and cached arm configuration
    pose_3 = geometry_msgs.msg.Pose()
    pose_3.position.x = 0.6188265189947368
    pose_3.position.y = 0.00047685411945365885
    pose_3.position.z = 0.9994083078217597
    pose_3.orientation.x = 0.7289562364724991
    pose_3.orientation.y = 0.000545133456572109
    pose_3.orientation.z = 0.6845598375391445
    pose_3.orientation.w = 0.0005804875061127526

    return [pose_1, pose_2, pose_3]


@pytest.fixture(scope="module", autouse=True)
def user_forced_request():
    joints_tool_short = [
        0.000353271,
        0.118332,
        0.189251,
        0.00190539,
        -0.244792,
        -0.00341686,
    ]

    service_request = MovejUserIKServiceRequest()
    service_request.cached_joints = joints_tool_short
    service_request.arm_config = ArmConfigs.FUT
    service_request.rev_count = 0
    return service_request


def test_short_tool_valid_cache(
    launcher, move_ik_service, user_forced_request, poses
):
    assert launcher.cycle_start()
    user_forced_request.pose = poses[0]
    response = move_ik_service(user_forced_request)
    assert response.success
    assert response.is_user_specification_coherent


def test_similar_short_tool_valid_cache(
    launcher, move_ik_service, user_forced_request, poses
):
    assert launcher.cycle_start()
    user_forced_request.pose = poses[1]
    response = move_ik_service(user_forced_request)
    assert response.success
    assert response.is_user_specification_coherent


def test_long_tool_invalid_cache(
    launcher, move_ik_service, user_forced_request, poses
):
    assert launcher.cycle_start()
    user_forced_request.pose = poses[2]
    response = move_ik_service(user_forced_request)
    assert response.success
    assert not response.is_user_specification_coherent

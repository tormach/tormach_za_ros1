#!/usr/bin/env python

# Check if robot arm configurations are correctly handled by the robot_config_service ROS service.
# The end-effector is frequently placed in front or behind the z1 axis that defines shoulder configuration
# A welding torch tool_frame is also chosen to check if the shoulder configuration will be updated correctly

# Note that convention used by Fanuc that we use deviates from the opw_kinematics convention
# for shoulder front/back setting.Fanuc convention uses tool frame to determine shoulder configuration,
# while opw_kinematics uses wrist center to determine shoulder front/back configuration.

import pytest

from robot_test.helpers import start_program
from robot_test.utils.arm_config_handler import ArmConfigHandler

from movej_ik_server_msgs.msg import ArmConfigs


def program():
    from robot_command.rpl import (  # noqa: F401
        set_units,
        movej,
        j,
        pause,
        set_tool_frame,
        change_tool_frame,
        Pose,
    )

    import PyKDL

    set_units("mm", "rad", "s")

    # welding torch tool transform
    # transl [m]: 0.0214 0 0.355
    # rot quat: w: 0.909628 xyz: 0.0 0.415423 0.0
    # rot axis-angle: xyz: 0 1 0 angle: 0.856815

    x, y, z, w = 0.0, 0.415423, 0.0, 0.909628
    rotation = PyKDL.Rotation.Quaternion(x, y, z, w)

    translation = PyKDL.Vector(21.4, 0.0, 355.0)

    # use this transform if you wish to reorient the welding tool aruond z6 axis of the J6 flange
    # frame_pi_rotation = PyKDL.Frame(PyKDL.Rotation.RotZ(np.pi), PyKDL.Vector(0.0, 0.0, 0.0))
    # welding_torch_tool = Pose.from_kdl_frame(frame_pi_rotation * PyKDL.Frame(rotation, translation))

    welding_torch_tool = Pose.from_kdl_frame(PyKDL.Frame(rotation, translation))
    set_tool_frame("welding_torch_tool", welding_torch_tool)

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))

    def main():
        pause()
        movej(j[0.0, -0.65, 0.0, 0.0, -1.5708, 0.0])

        change_tool_frame("welding_torch_tool")
        pause()
        change_tool_frame("flange_frame")
        pause()
        movej(j[0.0, -0.50, 0.0, 0.0, -1.5708, 0.0])
        change_tool_frame("welding_torch_tool")
        pause()
        change_tool_frame("flange_frame")
        pause()
        movej(j[0.0, 0.0, 0.0, 0.0, 1.5708, 0.0])
        change_tool_frame("welding_torch_tool")
        pause()
        change_tool_frame("flange_frame")
        pause()
        movej(j[0.0, -0.9, 0.0, 0.0, 0.9, 0.0])
        change_tool_frame("welding_torch_tool")
        pause()
        change_tool_frame("flange_frame")
        pause()
        movej(j[0.0, -1.0, 0.0, 0.0, 1.0, 0.0])
        change_tool_frame("welding_torch_tool")
        pause()
        change_tool_frame("flange_frame")
        pause()
        movej(j[0.0, 0.0, 0.0, 0.0, 0.8, 0.0])
        change_tool_frame("welding_torch_tool")
        pause()
        change_tool_frame("flange_frame")
        pause()


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
    ArmConfigs.FUB,
    ArmConfigs.FUB,
    ArmConfigs.FUB,
    ArmConfigs.FUT,
    ArmConfigs.NUT,
    ArmConfigs.NUT,
    ArmConfigs.NUT,
    ArmConfigs.NUT,
    ArmConfigs.NUT,
    ArmConfigs.NUB,
    ArmConfigs.NUT,
    ArmConfigs.NUT,
]
rev_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
test_numbers = range(len(robot_configs))

test_data = list(zip(robot_configs, rev_counts, test_numbers))


@pytest.mark.parametrize("config,rev_count,test_number", test_data)
def test_configs(launcher, arm_config_handler, config, rev_count, test_number):
    assert launcher.cycle_start()
    config_string, count = arm_config_handler.get_config()
    assert (
        config_string == config
    ), f"Test {test_number} failed: Expected config: {config}, got {config_string}"
    assert (
        count == rev_count
    ), f"Test {test_number} failed: Expected rev_count: {rev_count}, got {count}"

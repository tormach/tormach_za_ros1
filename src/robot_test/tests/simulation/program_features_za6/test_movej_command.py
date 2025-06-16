import pytest
from math import radians

from robot_test.helpers import start_program
from robot_command.rpl import Pose


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        pause,
        set_path_blending,
        sleep,
        p,
        Pose,
        Joints,
    )

    set_units("mm", "deg")

    # fmt: off
    movej_1 = p[298.78851771354675, -516.9166326522827, 540.5328869819641, 161.13781669674404, -0.0002853289712675753, 0.00013517956643081233]
    movej_2 = p[790.595531463623, 101.63775831460953, 406.90919756889343, -97.89178741637505, -30.94304127904307, -79.72532263027507]
    movej_3 = p[440.46953320503235, 235.17285287380219, 599.4446873664856, -148.68719144186156, 18.0416434440235, -85.98704867127738]
    movej_4 = p[462.4345302581787, -47.149982303380966, 503.5162568092346, -143.09677563244813, -34.60072711010529, -119.7480216325828]
    # fmt: on

    def main():
        # test_movej_to_all_zeros_global_waypoint_works
        pause()
        movej("all_zeros")

        # test_movej_to_local_joints_waypoint_is_within_tolerance_limit
        pause()
        movej(Joints(j2=20.3, j4=-10.2, j6=2.34))

        # test_movej_to_local_pose_waypoint_is_within_tolerance_limit
        pause()
        movej(Pose(x=500, z=450, a=179))
        sleep(0.1)  # without this, feedback pos can be outside of tolerance

        # test_movej_between_waypoints_without_path_blending_works
        pause()
        movej(movej_1)
        movej(movej_2)
        movej(movej_3)
        movej(movej_4)

        # test_movej_between_waypoints_with_path_blending_works
        pause()
        set_path_blending(enable=True, blend_radius=0.0)
        movej(movej_1)
        movej(movej_2)
        movej(movej_3)
        movej(movej_4)
        set_path_blending(enable=False)

        exit()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.mark.dependency()
def test_movej_to_all_zeros_global_waypoint_works(launcher):
    assert launcher.cycle_start()


@pytest.mark.dependency(
    depends=['test_movej_to_all_zeros_global_waypoint_works']
)
def test_movej_to_local_joints_waypoint_is_within_tolerance_limit(
    launcher, joints_to_pose_interface, config
):
    assert launcher.cycle_start()

    joint_values = joints_to_pose_interface.get_current_joint_values()
    joint_tolerance = config.get_param('/moveit/goal_joint_tolerance')
    assert joint_values[0] == pytest.approx(0.0, abs=joint_tolerance)
    assert joint_values[1] == pytest.approx(radians(20.3), abs=joint_tolerance)
    assert joint_values[2] == pytest.approx(0.0, abs=joint_tolerance)
    assert joint_values[3] == pytest.approx(radians(-10.2), abs=joint_tolerance)
    assert joint_values[4] == pytest.approx(0.0, abs=joint_tolerance)
    assert joint_values[5] == pytest.approx(radians(2.34), abs=joint_tolerance)


@pytest.mark.dependency(
    depends=['test_movej_to_local_joints_waypoint_is_within_tolerance_limit']
)
def test_movej_to_local_pose_waypoint_is_within_tolerance_limit(
    launcher, joints_to_pose_interface, config
):
    assert launcher.cycle_start()

    ros_pose = joints_to_pose_interface.get_current_pose().pose
    pose = Pose.from_ros_pose(ros_pose)
    pos_tolerance = config.get_param('/moveit/goal_position_tolerance')
    ori_tolerance = config.get_param('/moveit/goal_orientation_tolerance')
    assert pose.x == pytest.approx(0.499973002355918, abs=pos_tolerance)
    assert pose.y == pytest.approx(0.0009994832478904883, abs=pos_tolerance)
    assert pose.z == pytest.approx(0.44998255395356523, abs=pos_tolerance)
    assert pose.a == pytest.approx(radians(179), abs=ori_tolerance)
    assert pose.b == pytest.approx(0.0, abs=ori_tolerance)
    assert pose.c == pytest.approx(0.0, abs=ori_tolerance)


@pytest.mark.dependency(
    depends=['test_movej_to_local_joints_waypoint_is_within_tolerance_limit']
)
def test_movej_between_waypoints_without_path_blending_works(launcher):
    assert launcher.cycle_start()


@pytest.mark.dependency(
    depends=['test_movej_between_waypoints_without_path_blending_works']
)
def test_movej_between_waypoints_with_path_blending_works(launcher):
    assert launcher.cycle_start()

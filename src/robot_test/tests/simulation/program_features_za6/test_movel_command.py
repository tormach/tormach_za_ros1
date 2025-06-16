import pytest

from robot_test.helpers import start_program


def program():
    from robot_command.rpl import (
        set_units,
        movej,
        movel,
        p,
        pause,
        set_path_blending,
    )

    set_units("mm", "deg")

    waypoint_1 = p[599.333, 219.276, 583.367, 166.435, -15.252, -48.973]
    waypoint_2 = p[876.611, -168.869, 429.993, -144.539, -16.800, -50.111]
    waypoint_3 = p[402.199, -128.235, 392.391, -180.000, -0.000, 0.000]
    waypoint_4 = p[350.000, -128.235, 392.391, -180.000, -0.000, 0.000]
    waypoint_5 = p[350.000, -0.000, 392.391, -180.000, -0.000, 0.000]
    waypoint_6 = p[400.000, 0.000, 392.391, -180.000, -0.000, 0.000]

    def main():
        # test_movel_move_to_prepare_pose_works
        pause()
        movej("all_zeros")
        movej(waypoint_1)

        # test_movel_between_waypoints_without_path_blending_works
        pause()
        movel(waypoint_2)
        movel(waypoint_3)

        # test_movel_between_waypoints_with_path_blending_zero_radius_works
        pause()
        set_path_blending(enable=True, blend_radius=0.0)
        movel(waypoint_4)
        movel(waypoint_5)
        movel(waypoint_6)
        set_path_blending(enable=False)

        # test_movel_between_waypoints_with_path_blending_and_radius_works
        pause()
        set_path_blending(enable=True, blend_radius=1.0)
        movel(waypoint_3)
        movel(waypoint_4)
        movel(waypoint_5)
        movel(waypoint_6)
        set_path_blending(enable=False)

        exit()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.mark.dependency()
def test_movel_move_to_prepare_pose_works(launcher):
    assert launcher.cycle_start()


@pytest.mark.dependency(dependency=['test_movel_move_to_prepare_pose_works'])
def test_movel_between_waypoints_without_path_blending_works(launcher):
    assert launcher.cycle_start()


@pytest.mark.dependency(
    dependency=['test_movel_between_waypoints_without_path_blending_works']
)
def test_movel_between_waypoints_with_path_blending_zero_radius_works(launcher):
    assert launcher.cycle_start()


@pytest.mark.dependency(
    dependency=[
        'test_movel_between_waypoints_with_path_blending_zero_radius_works'
    ]
)
def test_movel_between_waypoints_with_path_blending_and_radius_works(launcher):
    assert launcher.cycle_start()

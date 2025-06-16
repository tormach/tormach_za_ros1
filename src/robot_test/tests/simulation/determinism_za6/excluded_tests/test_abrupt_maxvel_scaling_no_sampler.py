#!/usr/bin/env python
"""
Test the movej between two goals on a plane parallel to XY plane
Change the maxvel slider value and check the execution time
Check if moves originally planned with `velocity_scale`
Greater than allowed maxvel are scaled down
Results are not perfectly linear, so allow for some deviation
"""
import pytest

from robot_test.helpers import start_program
from robot_test.utils.config_manager_publisher import ConfigManagerPublisher
from robot_test.utils.velocity_transition_handler import (
    VelocityTransitionHandler,
)

import time

MAXVEL_SCALE_PARAMETER = "user_config/maxvel_scale"
WAIT_TIME = 1.0


def program():
    from robot_command.rpl import (  # noqa: F401
        set_units,
        movej,
        movel,
        j,
        p,
        pause,
        set_tool_frame,
        change_tool_frame,
        Pose,
    )

    import PyKDL

    set_units("mm", "rad", "s")

    flange_frame = PyKDL.Frame(
        PyKDL.Rotation.RotZ(0.0), PyKDL.Vector(0.0, 0.0, 0.0)
    )
    set_tool_frame("flange_frame", Pose.from_kdl_frame(flange_frame))
    change_tool_frame("flange_frame")

    def main():
        set_units("mm", "rad", "s")
        movej(j[0.0, 0.0, 0.0, 0.0, 1.5708, 0.0], velocity_scale=1.0)
        movej(p[600.0, -300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=1.0)

        while True:
            # 100% speed
            pause()
            # movej(j[0.46, 0.7013, -0.0418, -0.018, 0.9120, 0.4650], velocity_scale=1.0)
            movej(p[600.0, 300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=1.0)

            # 75% speed
            pause()
            # movej(j[0.46, 0.7013, -0.0418, -0.018, 0.9120, 0.4650], velocity_scale=0.25)
            movej(p[600.0, -300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=0.75)

            # 50% speed
            pause()
            # movej(j[0.46, 0.7013, -0.0418, -0.018, 0.9120, 0.4650], velocity_scale=0.25)
            movej(p[600.0, 300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=0.5)

            # 25% speed
            pause()
            # movej(j[0.46, 0.7013, -0.0418, -0.018, 0.9120, 0.4650], velocity_scale=0.10)
            movej(p[600.0, -300.0, 450.0, 3.14, 0.0, 0.0], velocity_scale=0.25)


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.fixture(scope="module", autouse=True)
def vel_slider():
    """
    Modify parameters in the config manager
    """
    vel_slider = ConfigManagerPublisher()
    return vel_slider


@pytest.fixture(scope="module", autouse=True)
def vel_transition():
    vel_transition = VelocityTransitionHandler()
    transition_time = 0.2
    vel_transition.set_transition_time(transition_time)
    time.sleep(WAIT_TIME)
    return vel_transition


execution_times = []
CYCLES_PER_LOOP = 4


@pytest.mark.dependency()
def test_maxvel_scale_1_00(launcher, vel_slider):
    vel_slider.publish_update(MAXVEL_SCALE_PARAMETER, "1.0", delay=0)
    time.sleep(WAIT_TIME)

    execution_times_row = []
    for i in range(CYCLES_PER_LOOP):
        start_time = time.time()
        assert launcher.cycle_start()
        end_time = time.time()

        elapsed_time = end_time - start_time
        execution_times_row.append(elapsed_time)

    execution_times.append(execution_times_row)


@pytest.mark.dependency(depends=['test_maxvel_scale_1_00'])
def test_maxvel_scale_0_75(launcher, vel_slider):
    vel_slider.publish_update(MAXVEL_SCALE_PARAMETER, "0.75", delay=0)
    time.sleep(WAIT_TIME)

    execution_times_row = []
    for i in range(CYCLES_PER_LOOP):
        start_time = time.time()
        assert launcher.cycle_start()
        end_time = time.time()

        elapsed_time = end_time - start_time
        execution_times_row.append(elapsed_time)

    execution_times.append(execution_times_row)


@pytest.mark.dependency(depends=['test_maxvel_scale_0_75'])
def test_maxvel_scale_0_50(launcher, vel_slider):
    vel_slider.publish_update(MAXVEL_SCALE_PARAMETER, "0.5", delay=0)
    time.sleep(WAIT_TIME)

    execution_times_row = []
    for i in range(CYCLES_PER_LOOP):
        start_time = time.time()
        assert launcher.cycle_start()
        end_time = time.time()

        elapsed_time = end_time - start_time
        execution_times_row.append(elapsed_time)

    execution_times.append(execution_times_row)


@pytest.mark.dependency(depends=['test_maxvel_scale_0_50'])
def test_maxvel_scale_0_25(launcher, vel_slider):
    vel_slider.publish_update(MAXVEL_SCALE_PARAMETER, "0.25", delay=0)
    time.sleep(WAIT_TIME)

    execution_times_row = []
    for i in range(CYCLES_PER_LOOP):
        start_time = time.time()
        assert launcher.cycle_start()
        end_time = time.time()

        elapsed_time = end_time - start_time
        execution_times_row.append(elapsed_time)

    execution_times.append(execution_times_row)


@pytest.mark.dependency(depends=['test_maxvel_scale_0_25'])
def test_check_vel_scale_1_00():
    column = [row[0] for row in execution_times]
    # exeuction time for maxvel slider value 1.0 is unafeected,
    # all others are affected

    assert column[1] == pytest.approx(column[0] * 1.0 / 0.75, abs=0.2)
    assert column[2] == pytest.approx(column[0] * 1.0 / 0.50, abs=0.3)
    assert column[3] == pytest.approx(column[0] * 1.0 / 0.25, abs=0.4)


@pytest.mark.dependency(depends=['test_maxvel_scale_0_25'])
def test_check_vel_scale_0_75():
    column = [row[1] for row in execution_times]

    # exeuction times for maxvel slider value 1.0 and 0.75 should be roughly equal and unafeected
    assert column[1] == pytest.approx(column[0] * 1.0, abs=0.2)

    assert column[2] == pytest.approx(column[0] * 0.75 / 0.50, abs=0.5)
    assert column[3] == pytest.approx(column[0] * 0.75 / 0.25, abs=0.5)


@pytest.mark.dependency(depends=['test_maxvel_scale_0_25'])
def test_check_vel_scale_0_50():
    column = [row[2] for row in execution_times]

    # exeuction times for maxvel slider value 1.0, 0.75, and 0.50 should be roughly equal and unafeected
    assert column[1] == pytest.approx(column[0] * 1.0, abs=0.2)
    assert column[2] == pytest.approx(column[0] * 1.0, abs=0.2)

    assert column[3] == pytest.approx(column[0] * 0.50 / 0.25, abs=0.5)


@pytest.mark.dependency(depends=['test_maxvel_scale_0_25'])
def test_check_vel_scale_0_25():
    column = [row[3] for row in execution_times]
    # all execution times should be roughly equal and unafeected
    assert all(
        element == pytest.approx(column[0], abs=0.3) for element in column
    )

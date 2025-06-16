import pytest
import rospy
from time import sleep

from robot_test.helpers import start_program

from machinekit import hal

IO_SYNC_TIME_S = 0.1


# [1]
# A robot program wrapped into a Python function
# this will be written to a file and executed by the robot program interpreter
def program():
    from robot_command.rpl import (
        set_units,
        pause,
        set_digital_out,
        get_digital_in,
    )

    set_units("mm", "deg")

    def main():
        # [2]
        # the robot program part of the first test case
        # note that it starts with a pause command
        #
        # test_set_digital_output_by_nr_works
        pause()
        set_digital_out(1, True)
        pause()
        set_digital_out(1, False)

        # [3]
        # the robot program part of the second test case
        #
        # test_set_digital_output_by_name_works
        pause()
        set_digital_out("spoil", False)
        pause()
        set_digital_out("spoil", True)

        # test_get_digital_output_by_nr_works
        pause()
        assert get_digital_in(3) is True
        pause()
        assert get_digital_in(3) is False

        # test_get_digital_input_by_name_works
        pause()
        assert get_digital_in("camera") is False
        pause()
        assert get_digital_in("camera") is True

        # [4]
        # when all test cases are completed we exit the robot program
        exit()


# [5]
# the robot_program fixture is loaded automatically with the module
# it starts the robot program
@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


# [6]
# the pytest part of the first test case
# note the cycle_start commands executing the robot program step by step
# we mark it as a dependency for additional test cases to provide an execution order
@pytest.mark.dependency()
def test_set_digital_output_by_nr_works(launcher):
    assert launcher.cycle_start()
    assert hal.Pin('hal_io.digital_out_1').get() is True
    assert launcher.cycle_start()
    assert hal.Pin('hal_io.digital_out_1').get() is False


# [7]
# this fixture prepares the environment
# note that we can also cleanup stuff after test completion by using yield
@pytest.fixture(scope="module")
def prepare_digital_io_names():
    digital_out_ns = 'io/digital_out_names'
    digital_out_names = rospy.get_param(digital_out_ns)
    temp_digital_out_names = {'spoil': 2}
    rospy.set_param(digital_out_ns, temp_digital_out_names)
    digital_in_ns = 'io/digital_in_names'
    digital_in_names = rospy.get_param(digital_in_ns)
    temp_digital_in_names = {'camera': 4}
    rospy.set_param(digital_in_ns, temp_digital_in_names)
    yield temp_digital_out_names
    rospy.set_param(digital_out_ns, digital_out_names)
    rospy.set_param(digital_in_ns, digital_in_names)


# [8]
# pytest part of the second test case
# note the dependency on the first test case to ensure execution order
@pytest.mark.dependency(depends=['test_set_digital_output_by_nr_works'])
def test_set_digital_output_by_name_works(launcher, prepare_digital_io_names):
    assert launcher.cycle_start()
    assert hal.Pin('hal_io.digital_out_2').get() is False
    assert launcher.cycle_start()
    assert hal.Pin('hal_io.digital_out_2').get() is True


def set_pin_or_signal(pin_name, value):
    pin = hal.Pin(pin_name)
    if pin.signal:
        pin.signal.set(value)
    else:
        pin.set(value)


@pytest.mark.dependency(depends=['test_set_digital_output_by_name_works'])
def test_get_digital_output_by_nr_works(launcher):
    set_pin_or_signal('hal_io.digital_in_3', True)
    sleep(IO_SYNC_TIME_S)
    assert launcher.cycle_start()
    set_pin_or_signal('hal_io.digital_in_3', False)
    sleep(IO_SYNC_TIME_S)
    assert launcher.cycle_start()


@pytest.mark.dependency(depends=['test_get_digital_output_by_nr_works'])
def test_get_digital_input_by_name_works(launcher, prepare_digital_io_names):
    set_pin_or_signal('hal_io.digital_in_4', False)
    sleep(IO_SYNC_TIME_S)
    assert launcher.cycle_start()
    set_pin_or_signal('hal_io.digital_in_4', True)
    sleep(IO_SYNC_TIME_S)
    assert launcher.cycle_start()

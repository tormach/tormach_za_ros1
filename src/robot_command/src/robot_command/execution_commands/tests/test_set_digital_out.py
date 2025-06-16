import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces import hal_io_interface
from robot_command.execution_commands import SetDigitalOut


@pytest.fixture  # noqa: F811
def io_interface(mocker):  # noqa: F811
    hal_io_interface.HalIoInterfaceSingleton._instance = None
    mocker.patch.object(hal_io_interface, 'HalIoInterface')
    return hal_io_interface.HalIoInterface()


@pytest.mark.parametrize('nr, count', [(5, 4), (0, 3), (-1, 307)])
def test_set_digital_out_with_io_nr_not_in_range_throws_value_error(
    nr, count, io_interface
):
    io_interface.digital_out_count = count

    with pytest.raises(ValueError):
        SetDigitalOut(nr, True)


@pytest.mark.parametrize(
    'nr, count, state', [(554, 554, True), (1, 619, False)]
)
def test_set_digital_out_with_nr_in_range_is_accepted(
    nr, count, state, io_interface
):
    io_interface.digital_out_count = count

    command = SetDigitalOut(nr, state)

    assert nr == command.nr
    assert state == command.state


def test_string_is_accepted_as_input_type(io_interface):
    io_interface.get_digital_output_nr.return_value = 476

    command = SetDigitalOut('renewed', False)

    assert command.nr == 476


def test_key_error_is_raised_when_name_does_not_exist(io_interface):
    io_interface.get_digital_output_nr.return_value = -1

    with pytest.raises(KeyError):
        SetDigitalOut('trinkums', True)


def test_passing_other_type_as_pin_number_values_raises_value_error():
    with pytest.raises(TypeError):
        SetDigitalOut(object(), False)

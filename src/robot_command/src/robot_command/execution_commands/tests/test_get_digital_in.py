import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces import hal_io_interface
from robot_command.execution_commands import GetDigitalIn


@pytest.fixture  # noqa: F811
def io_interface(mocker):  # noqa: F811
    hal_io_interface.HalIoInterfaceSingleton._instance = None
    mocker.patch.object(hal_io_interface, 'HalIoInterface')
    return hal_io_interface.HalIoInterface()


@pytest.mark.parametrize('nr, count', [(315, 314), (0, 103), (-1, 3)])
def test_get_digital_in_with_io_nr_not_in_range_throws_value_error(
    nr, count, io_interface
):
    io_interface.digital_in_count = count

    with pytest.raises(ValueError):
        GetDigitalIn(nr)


@pytest.mark.parametrize('nr, count', [(880, 880), (1, 331)])
def test_get_digital_in_with_nr_in_range_is_accepted(nr, count, io_interface):
    io_interface.digital_in_count = count

    command = GetDigitalIn(nr)

    assert nr == command.nr


def test_string_is_accepted_as_input_type(io_interface):
    io_interface.get_digital_input_nr.return_value = 1

    command = GetDigitalIn('quatrino')

    assert command.nr == 1


def test_key_error_is_raised_when_name_does_not_exist(io_interface):
    io_interface.get_digital_input_nr.return_value = -1

    with pytest.raises(KeyError):
        GetDigitalIn('refitted')


def test_passing_other_type_as_pin_number_values_raises_value_error():
    with pytest.raises(TypeError):
        GetDigitalIn(object())

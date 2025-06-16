import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces import hal_io_interface, interrupt_interface
from robot_command.execution_commands import RegisterInterrupt
from robot_command.rpl import InterruptSource


@pytest.fixture  # noqa: F811
def io_interface(mocker):  # noqa: F811
    hal_io_interface.HalIoInterfaceSingleton._instance = None
    mocker.patch.object(hal_io_interface, 'HalIoInterface')
    return hal_io_interface.HalIoInterface()


@pytest.fixture  # noqa: F811
def int_interface(mocker):  # noqa: F811
    interrupt_interface.InterruptInterfaceSingleton._instance = None
    mocker.patch.object(interrupt_interface, 'InterruptInterface')
    return interrupt_interface.InterruptInterface()


@pytest.mark.parametrize(
    'source, nr, count',
    [
        (InterruptSource.DigitalInput, 5, 4),
        (InterruptSource.DigitalInput, 0, 3),
        (InterruptSource.DigitalInput, -1, 307),
        (InterruptSource.UserIo, 453, 30),
        (InterruptSource.UserIo, -1, 9),
        (InterruptSource.Program, -1, 0),
    ],
)
def test_register_interrupt_with_nr_not_in_range_throws_value_error(
    source, nr, count, io_interface, int_interface
):
    if source is InterruptSource.DigitalInput:
        io_interface.digital_in_count = count
    else:
        io_interface.user_io_count = count

    with pytest.raises(ValueError):
        RegisterInterrupt(source, nr, None)


@pytest.mark.parametrize(
    'source, nr, count',
    [
        (InterruptSource.DigitalInput, 554, 554),
        (InterruptSource.DigitalInput, 1, 619),
        (InterruptSource.UserIo, 517, 860),
        (InterruptSource.UserIo, 1, 55),
        (InterruptSource.Program, 667, 0),
        (InterruptSource.Program, 1, 715),
    ],
)
def test_register_interrupt_with_correct_args_is_accepted(
    source, nr, count, io_interface, int_interface
):
    if source is InterruptSource.DigitalInput:
        io_interface.digital_in_count = count
    else:
        io_interface.user_io_count = count

    def fct():
        return None

    command = RegisterInterrupt(source, nr, fct)

    assert nr == command.nr
    assert source is command.source
    assert fct is command.fct


def test_string_is_accepted_as_input_type_for_digital_input(
    io_interface, int_interface
):
    io_interface.get_digital_input_nr.return_value = 73

    command = RegisterInterrupt(InterruptSource.DigitalInput, "broad", None)

    assert command.nr == 73


def test_key_error_is_raised_when_digital_input_name_does_not_exist(
    io_interface, int_interface
):
    io_interface.get_digital_input_nr.return_value = -1

    with pytest.raises(KeyError):
        RegisterInterrupt(InterruptSource.DigitalInput, "appear", None)


@pytest.mark.parametrize(
    'source, nr',
    [
        (InterruptSource.DigitalInput, object()),
        (324, 3),
        (InterruptSource.UserIo, "puzzle"),
        (InterruptSource.Program, 324.4),
    ],
)
def test_passing_wrong_types_raises_type_error(
    source, nr, io_interface, int_interface
):
    with pytest.raises(TypeError):
        RegisterInterrupt(source, nr)

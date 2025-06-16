import pytest

from robot_command.execution_commands.sleep import Sleep


@pytest.mark.parametrize('test_input', [166.21, 735, 0.0, 0])
def test_sleep_command_accepts_valid_time_arguments(test_input):
    sleep = Sleep(test_input)

    assert sleep.secs == test_input


@pytest.mark.parametrize('test_input', [-204.37, -11, "10", object()])
def test_sleep_command_fails_with_invalid_time_arguments(test_input):
    with pytest.raises(TypeError):
        Sleep(test_input)

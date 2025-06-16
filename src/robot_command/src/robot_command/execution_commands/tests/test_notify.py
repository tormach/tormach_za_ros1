import pytest

from robot_command.execution_commands.notify import Notify


@pytest.mark.parametrize('test_input', ["mcintosh", "wedding"])
def test_notify_command_accepts_valid_message_arguments(test_input):
    notify = Notify(test_input)

    assert notify.message == test_input


@pytest.mark.parametrize('test_input', [object(), False])
def test_notify_command_fails_with_invalid_message_arguments(test_input):
    with pytest.raises(TypeError):
        Notify(test_input)

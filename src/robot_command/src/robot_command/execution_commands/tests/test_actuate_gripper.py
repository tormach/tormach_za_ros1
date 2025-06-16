import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces import gripper_interface as gripper_if
from robot_command.execution_commands import ActuateGripper


@pytest.fixture  # noqa: F811
def gripper_interface(mocker):  # noqa: F811
    gripper_if.GripperInterfaceSingleton._instance = None
    mocker.patch.object(gripper_if, 'GripperInterface')
    return gripper_if.GripperInterface()


def test_actuate_gripper_without_configured_gripper_raises_runtime_error(
    gripper_interface,
):
    gripper_interface.configured = False

    with pytest.raises(RuntimeError):
        ActuateGripper(0.5)


@pytest.mark.parametrize(
    'position, effort, wait',
    [(-0.1, 0.2, True), (0.0, 0.0, '1'), (1.0, 2.0, True)],
)
def test_actuate_gripper_with_wrong_arguments_raises_value_error(
    gripper_interface, position, effort, wait
):
    with pytest.raises((ValueError, TypeError)):
        ActuateGripper(position, effort, wait)

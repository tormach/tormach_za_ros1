import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces import config_interface
from robot_command.execution_commands import SetUnits


@pytest.fixture  # noqa: F811
def conf_interface(mocker):  # noqa: F811
    config_interface.ConfigInterfaceSingleton._instance = None
    mocker.patch.object(config_interface, 'ConfigInterface')
    return config_interface.ConfigInterface()


@pytest.mark.parametrize(
    'linear_unit, angular_unit, time_unit',
    [
        ("3fd", None, None),
        (None, "gs9ye2", None),
        ("f0v78499", "yTDr2y", None),
        ("deg", None, None),
        (None, "mm", None),
        (None, None, "GFtF"),
        (None, None, "m"),
    ],
)
def test_set_unit_with_unsupported_unit_type_throws_value_error(
    linear_unit, angular_unit, time_unit, conf_interface
):
    with pytest.raises(TypeError):
        SetUnits(linear_unit, angular_unit, time_unit)


@pytest.mark.parametrize(
    'linear_unit, angular_unit, time_unit',
    [
        ("mm", None, None),
        (None, "deg", None),
        (None, None, "min"),
        ("in", "rad", None),
        ("km", "radian", None),
        ("in", "deg", "seconds"),
    ],
)
def test_set_unit_with_supported_unit_type_is_created_correctly(
    linear_unit, angular_unit, time_unit, conf_interface
):
    assert SetUnits(linear_unit, angular_unit, time_unit)
    assert SetUnits(angular=angular_unit, linear=linear_unit, time=time_unit)

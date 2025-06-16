from math import pi

import pytest

from robot_ui.pathpilot.robot import Units


@pytest.fixture()
def units():
    return Units()


def test_converting_linear_unit_from_ros_works(units):
    assert pytest.approx(units.fromRos(0.0254, 'in')) == 1.0


def test_converting_linear_unit_to_ros_works(units):
    assert pytest.approx(units.toRos(253.00, 'mm')) == 0.253


def test_converting_angular_unit_from_ros_works(units):
    assert pytest.approx(units.fromRos(pi, 'deg')) == 180


def test_converting_angular_unit_from_to_works(units):
    assert pytest.approx(units.fromTo(90, 'deg', 'rad')) == pi / 2


def test_converting_angular_unit_to_ros_works(units):
    assert pytest.approx(units.toRos(90, 'deg')) == pi / 2


def test_converting_velocity_from_ros_works(units):
    assert pytest.approx(units.fromRos(1.6, 'mm/s')) == 1600


def test_converting_velocity_from_to_works(units):
    assert pytest.approx(units.fromTo(1.0, 'in/s', 'mm/min')) == 1524


def test_converting_velocity_to_ros_works(units):
    assert pytest.approx(units.toRos(10.0, 'in/min')) == 0.00423333


def test_converting_acceleration_from_ros_works(units):
    assert pytest.approx(units.fromRos(0.183, 'mm/s^2')) == 183


def test_converting_acceleration_to_ros_works(units):
    assert pytest.approx(units.toRos(100.0, 'in/s^2')) == 2.54


def test_converting_acceleration_from_to_works(units):
    assert pytest.approx(units.fromTo(1.0, 'in/s^2', 'mm/s^2')) == 25.4

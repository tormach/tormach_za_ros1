import pytest

from robot_command.rpl import Joints
from robot_command.rpl.units import ureg


def test_creating_joints_from_list_works():
    data = [-4.98, 387.64, 932.94, -117.68, 70.19, 482.57]
    joints = Joints.from_list(data)

    assert joints.j1 == pytest.approx(-4.98)
    assert joints.j2 == pytest.approx(387.64)
    assert joints.j3 == pytest.approx(932.94)
    assert joints.j4 == pytest.approx(-117.68)
    assert joints.j5 == pytest.approx(70.19)
    assert joints.j6 == pytest.approx(482.57)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            (Joints(845.19, -280.62, 624.68, -451.37, 594.12, 220.93), None),
            Joints(
                845.19 * ureg.rad,
                -280.62 * ureg.rad,
                624.68 * ureg.rad,
                -451.37 * ureg.rad,
                594.12 * ureg.rad,
                220.93 * ureg.rad,
            ),
        ),
        (
            (Joints(j1=0.39 * ureg.rad), ureg.deg),
            Joints(j1=22.34535 * ureg.deg),
        ),
    ],
)
def test_with_units_adds_units_to_joints(test_input, expected):
    output = test_input[0].with_units(test_input[1])

    def quantity_compare(x, y):
        if x == 0.0:
            return x == y
        else:
            return (
                x.magnitude == pytest.approx(y.magnitude) and x.units == y.units
            )

    assert quantity_compare(output.j1, expected.j1)
    assert quantity_compare(output.j2, expected.j2)
    assert quantity_compare(output.j3, expected.j3)
    assert quantity_compare(output.j4, expected.j4)
    assert quantity_compare(output.j5, expected.j5)
    assert quantity_compare(output.j6, expected.j6)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            (
                Joints(
                    190.22 * ureg.rad,
                    271.28 * ureg.rad,
                    500.81 * ureg.rad,
                    533.97 * ureg.rad,
                    801.88 * ureg.rad,
                    670.81 * ureg.rad,
                ),
                None,
            ),
            Joints(190.22, 271.28, 500.81, 533.97, 801.88, 670.81),
        ),
        ((Joints(j4=0.411 * ureg.rad), ureg.deg), Joints(j4=23.548565)),
    ],
)
def test_without_units_removes_units_from_joints(test_input, expected):
    output = test_input[0].without_units(test_input[1])

    assert output.j1 == pytest.approx(expected.j1)
    assert output.j2 == pytest.approx(expected.j2)
    assert output.j3 == pytest.approx(expected.j3)
    assert output.j4 == pytest.approx(expected.j4)
    assert output.j5 == pytest.approx(expected.j5)
    assert output.j6 == pytest.approx(expected.j6)

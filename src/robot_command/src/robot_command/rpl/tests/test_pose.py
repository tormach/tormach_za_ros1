import pytest

from robot_command.rpl import Pose, PoseFactory
from robot_command.rpl.units import ureg


def test_creating_pose_from_list_works():
    data = [616.67, 813.47, 984.86, -227.30, 580.22, -730.87]
    pose = Pose.from_list(data)

    assert pose.x == pytest.approx(616.67)
    assert pose.y == pytest.approx(813.47)
    assert pose.z == pytest.approx(984.86)
    assert pose.a == pytest.approx(-227.30)
    assert pose.b == pytest.approx(580.22)
    assert pose.c == pytest.approx(-730.87)


def test_creating_pose_from_list_with_frame_works():
    data = [332.41, 560.85, 522.12, 139.73, 700.11, 514.80, "correct"]
    pose = Pose.from_list(data)

    assert pose.frame == "correct"


@pytest.mark.parametrize(
    "test_input",
    [
        [561.07, 848.78, 341.78, 932.50, 402.11, 59.50],
        [70.71, 72.47, 932.91, 95.49, 277.40, 25.38, "article"],
        [588.76 * ureg.mm, 602.89, 831.98, 589.80 * ureg.deg, 673.53, 483.39],
    ],
)
def test_creating_pose_from_correct_data_with_factory_works(test_input):
    p = PoseFactory()

    pose = p.__getitem__(test_input)

    assert isinstance(pose, Pose)


@pytest.mark.parametrize(
    "test_input",
    [
        [696.81, 92.28, 585.09, 734.05, 18.29],
        [696.81, 92.28, 585.09, 734.05, "cQHtQkHt"],
    ],
)
def test_creating_pose_from_incorrect_data_with_factory_throws_value_error(
    test_input,
):
    p = PoseFactory()

    with pytest.raises(ValueError):
        _ = p.__getitem__(test_input)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            (
                Pose(
                    x=104.06, y=721.42, z=-49.12, a=910.91, b=414.79, c=245.29
                ),
                None,
                None,
            ),
            Pose(
                x=104.06 * ureg.m,
                y=721.42 * ureg.m,
                z=-49.12 * ureg.m,
                a=910.91 * ureg.rad,
                b=414.79 * ureg.rad,
                c=245.29 * ureg.rad,
            ),
        ),
        ((Pose(y=599.15 * ureg.mm), ureg.m, None), Pose(y=0.59915 * ureg.m)),
        (
            (Pose(a=-0.196 * ureg.rad), None, ureg.deg),
            Pose(a=-11.2299727846 * ureg.deg),
        ),
    ],
)
def test_with_units_adds_units_to_pose(test_input, expected):
    output = test_input[0].with_units(test_input[1], test_input[2])

    def quantity_compare(x, y):
        if x == 0.0:
            return x == y
        else:
            return (
                x.magnitude == pytest.approx(y.magnitude) and x.units == y.units
            )

    assert quantity_compare(output.x, expected.x)
    assert quantity_compare(output.y, expected.y)
    assert quantity_compare(output.z, expected.z)
    assert quantity_compare(output.a, expected.a)
    assert quantity_compare(output.b, expected.b)
    assert quantity_compare(output.c, expected.c)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            (
                Pose(
                    x=11.90 * ureg.m,
                    y=969.03 * ureg.m,
                    z=131.40 * ureg.m,
                    a=990.95 * ureg.rad,
                    b=689.84 * ureg.rad,
                    c=600.55 * ureg.rad,
                ),
                None,
                None,
            ),
            Pose(x=11.9, y=969.03, z=131.4, a=990.95, b=689.84, c=600.55),
        ),
        ((Pose(z=0.24891 * ureg.m), ureg.mm, None), Pose(z=248.91)),
    ],
)
def test_without_units_removes_units_from_pose(test_input, expected):
    output = test_input[0].without_units(test_input[1], test_input[2])

    assert output.x == pytest.approx(expected.x)
    assert output.y == pytest.approx(expected.y)
    assert output.z == pytest.approx(expected.z)
    assert output.a == pytest.approx(expected.a)
    assert output.b == pytest.approx(expected.b)
    assert output.c == pytest.approx(expected.c)

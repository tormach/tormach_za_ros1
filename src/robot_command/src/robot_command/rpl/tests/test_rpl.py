import pytest

from robot_command import rpl


def test_creating_pose_from_six_floats_works():
    pose = rpl.p[0.1, int(-5), 2.3, float(3.4), 10, 6.7]

    assert isinstance(pose, rpl.Pose)


@pytest.mark.parametrize(
    "test_input",
    [[1, 2, 3, 4, 5], [7, 6, 5, 4, 3, 2, 1], "foo", [1, 2, 3, 4, 5, '6']],
)
def test_creating_pose_with_invalid_input_data_fails(test_input):
    with pytest.raises(ValueError):
        rpl.p.__getitem__(test_input)


def test_creating_joints_from_six_numbers_works():
    result = rpl.j[0.1, -1, float(-2.3), 3.4, int(4), 6.7]

    assert isinstance(result, rpl.Joints)


@pytest.mark.parametrize(
    "test_input",
    [[1, 2, 3, 4, 5], [7, 6, 5, 4, 3, 2, 1], "foo", [1, 2, 3, 4, 5, '6']],
)
def test_creating_joints_with_invalid_input_data_fails(test_input):
    with pytest.raises(ValueError):
        rpl.j.__getitem__(test_input)

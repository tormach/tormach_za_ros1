import pytest

from robot_command.interfaces import frame_interface
from robot_command.execution_commands.user_frame import UserFrame
from robot_command.rpl import Pose


@pytest.fixture  # noqa: F811
def frame_if(mocker):  # noqa: F811
    frame_interface.UserFrameInterfaceSingleton._instance = None
    mocker.patch.object(frame_interface, 'UserFrameInterface')
    return frame_interface.UserFrameInterface()


def test_frame_command_accepts_valid_pose_argument(frame_if):
    pose = Pose(x=826.91, y=334.53, z=503.21, a=965.18, b=322.75, c=983.05)

    frame = UserFrame(pose)

    assert frame.pose == pose


def test_frame_command_uses_xyz_of_position(frame_if):
    pose = Pose(x=826.91, y=334.53, z=503.21, a=965.18, b=322.75, c=983.05)

    frame = UserFrame(position=pose)

    assert frame.pose.x == pytest.approx(pose.x)
    assert frame.pose.y == pytest.approx(pose.y)
    assert frame.pose.z == pytest.approx(pose.z)
    assert frame.pose.a == 0.0
    assert frame.pose.b == 0.0
    assert frame.pose.c == 0.0


def test_frame_command_uses_abc_of_orientation(frame_if):
    pose = Pose(x=826.91, y=334.53, z=503.21, a=965.18, b=322.75, c=983.05)

    frame = UserFrame(orientation=pose)

    assert frame.pose.x == 0.0
    assert frame.pose.y == 0.0
    assert frame.pose.z == 0.0
    assert frame.pose.a == pytest.approx(pose.a)
    assert frame.pose.b == pytest.approx(pose.b)
    assert frame.pose.c == pytest.approx(pose.c)


@pytest.mark.parametrize('test_input', [(object(), None, None)])
def test_frame_command_fails_with_invalid_message_arguments(
    test_input, frame_if
):
    with pytest.raises(TypeError):
        UserFrame(test_input[0], test_input[1], test_input[2])

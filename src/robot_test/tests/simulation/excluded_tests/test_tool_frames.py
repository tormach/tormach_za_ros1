import pytest
import rospy
from math import radians
from std_msgs.msg import String

from robot_test.helpers import start_program

ACTIVE_FRAME_TOPIC = "/tool_frames/active"
MESSAGE_WAIT_TIMEOUT_S = 1.0


def program():
    import pytest
    from robot_command.rpl import (
        Pose,
        set_units,
        pause,
        set_tool_frame,
        get_tool_frame,
        change_tool_frame,
    )

    set_units("mm", "deg")

    def main():
        # test_setting_tool_frame_works
        pause()
        pose = Pose(y=746.16, a=97.48)
        set_tool_frame("_test_zP54uGN", pose)

        # test_getting_tool_frame_works
        pause()
        assert pose == get_tool_frame(
            "_test_zP54uGN"
        ), "Set and get frames did not match."

        # test_changing_tool_frame_works
        pause()
        change_tool_frame("_test_zP54uGN")
        pause()
        change_tool_frame("")

        # test_clearing_user_frame_works
        pause()
        set_tool_frame("_test_zP54uGN", None)
        with pytest.raises(TypeError, message="Could not delete tool frame."):
            _ = get_tool_frame("_test_zP54uGN")

        exit()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.mark.dependency()
def test_setting_tool_frame_works(launcher, config):
    assert launcher.cycle_start()
    data = config.get_param('/tool_frames/_test_zP54uGN')
    assert data is not None
    pose = data['pose']
    assert pose[1] == pytest.approx(0.74616)
    assert pose[3] == pytest.approx(radians(97.48))


@pytest.mark.dependency(depends=['test_setting_tool_frame_works'])
def test_getting_tool_frame_works(
    launcher,
):
    assert launcher.cycle_start()


def get_active_frame():
    return rospy.wait_for_message(
        ACTIVE_FRAME_TOPIC, String, timeout=MESSAGE_WAIT_TIMEOUT_S
    ).data


@pytest.mark.dependency(depends=['test_getting_tool_frame_works'])
def test_changing_tool_frame_works(launcher):
    assert launcher.cycle_start()
    assert get_active_frame() == '_test_zP54uGN'
    assert launcher.cycle_start()
    assert get_active_frame() == ''


@pytest.mark.dependency(depends=['test_changing_tool_frame_works'])
def test_clearing_tool_frame_works(launcher, config):
    assert launcher.cycle_start()
    data = config.get_param('/tool_frames/')
    assert '_test_zP54uGN' not in data

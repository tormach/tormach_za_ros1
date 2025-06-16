import pytest
import rospy

from math import radians
from std_msgs.msg import String

from robot_test.helpers import start_program

ACTIVE_FRAME_TOPIC = "/user_frames/active"
MESSAGE_WAIT_TIMEOUT_S = 1.0


def program():
    import pytest
    from robot_command.rpl import (
        Pose,
        set_units,
        pause,
        sync,
        set_user_frame,
        get_user_frame,
        change_user_frame,
        user_frame,
    )

    set_units("mm", "deg")

    def main():
        # test_setting_user_frame_works
        pause()
        pose = Pose(x=638.98, b=256.36)
        set_user_frame("_test_tcL7V", pose)

        # test_getting_user_frame_works
        pause()
        assert pose == get_user_frame(
            "_test_tcL7V"
        ), "Set and get frames did not match."

        # test_changing_user_frame_works
        pause()
        change_user_frame("_test_tcL7V")
        pause()
        change_user_frame("")

        # test_clearing_user_frame_works
        pause()
        set_user_frame("_test_tcL7V", None)
        with pytest.raises(TypeError, message="Could not delete user frame."):
            _ = get_user_frame("_test_tcL7V")

        # test_applying_temporary_user_frame_works
        pause()
        with user_frame(Pose(z=454.57)):
            pause()
            sync()  # pause halts before the next statement

        exit()


@pytest.fixture(scope="module", autouse=True)
def robot_program(launcher, tmpdir_factory):
    yield from start_program(program, launcher, tmpdir_factory)


@pytest.mark.dependency()
def test_setting_user_frame_works(launcher, config):
    assert launcher.cycle_start()
    data = config.get_param('/user_frames/_test_tcL7V')
    assert data is not None
    pose = data['pose']
    assert pose[0] == pytest.approx(0.63898)
    assert pose[4] == pytest.approx(radians(256.36))


@pytest.mark.dependency(depends=['test_setting_user_frame_works'])
def test_getting_user_frame_works(launcher):
    assert launcher.cycle_start()


def get_active_frame():
    return rospy.wait_for_message(
        ACTIVE_FRAME_TOPIC, String, timeout=MESSAGE_WAIT_TIMEOUT_S
    ).data


@pytest.mark.dependency(depends=['test_getting_user_frame_works'])
def test_changing_user_frame_works(launcher):
    assert launcher.cycle_start()
    assert get_active_frame() == '_test_tcL7V'
    assert launcher.cycle_start()
    assert get_active_frame() == ''


@pytest.mark.dependency(depends=['test_changing_user_frame_works'])
def test_clearing_user_frame_works(launcher, config):
    assert launcher.cycle_start()
    data = config.get_param('/user_frames/')
    assert '_test_tcL7V' not in data


@pytest.mark.dependency(depends=['test_clearing_user_frame_works'])
def test_applying_temporary_user_frame_works(launcher):
    assert launcher.cycle_start()
    assert get_active_frame() == '_stack'
    assert launcher.cycle_start()
    assert get_active_frame() == ''

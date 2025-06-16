import pytest
import rospy

from unittest.mock import MagicMock


def patch_rospy():
    import redis_store
    import tf2_ros

    rospy.get_param = lambda key, default=None: {}
    rospy.Service = MagicMock()
    rospy.Publisher = MagicMock()
    rospy.Timer = MagicMock()
    rospy.Time = MagicMock()
    redis_store.ConfigClient = MagicMock()
    rospy.set_param = MagicMock()
    tf2_ros.TransformBroadcaster = MagicMock()


@pytest.fixture
def publisher():
    patch_rospy()
    from robot_frame import FramePublisher

    publisher = FramePublisher('test_frames', 'home')
    yield publisher
    publisher.stop()


def test_frames_are_loaded_correctly_from_config(publisher):
    publisher._config.get_param = lambda key: {
        'chest': {
            'pose': [0, 1, 2, 3, 4, 5],
            'data': {'description': "exchange"},
        }
    }

    publisher._on_config_update_received('test_frames', 'O5d')

    assert len(publisher._frames) == 1
    assert publisher._frames['chest'].pose == pytest.approx([0, 1, 2, 3, 4, 5])


def test_broken_frames_are_ignored(publisher):
    publisher._config.get_param = lambda key: {'pray': 231423.3}

    publisher._on_config_update_received('test_frames', 'O5d')

    assert len(publisher._frames) == 0

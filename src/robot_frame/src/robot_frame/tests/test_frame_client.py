import pytest
import rospy
from std_msgs.msg import String

from unittest.mock import MagicMock


def patch_rospy():
    import redis_store

    rospy.get_param = lambda key, default=None: []
    rospy.ServiceProxy = MagicMock()
    rospy.Subscriber = MagicMock()
    rospy.wait_for_message = lambda *args, **kwargs: String("")
    redis_store.ConfigClient = MagicMock()
    rospy.set_param = MagicMock()


@pytest.fixture
def client():
    patch_rospy()
    from robot_frame import FrameClient

    client = FrameClient('test_frames')
    return client


def test_set_frame_sets_param_via_config_client(client):
    client.set_frame(
        name="kick",
        pose=[7.87, 163.53, 556.78, 323.37, 72.15, 694.65],
        data={'description': "width shoulder"},
    )

    assert client._config.set_param.call_count == 1
    name = client._config.set_param.call_args.args[0]
    item = client._config.set_param.call_args.args[1]
    assert name == "test_frames/kick"
    assert isinstance(item, dict)
    assert item['pose'] == pytest.approx(
        [7.87, 163.53, 556.78, 323.37, 72.15, 694.65]
    )
    assert item['data'] == {"description": "width shoulder"}


def test_set_frame_reuses_existing_description_if_not_set(client):
    client._subscribed = True
    client._frames = {
        'toward': {
            'pose': [783.92, 999.25, 685.98, 7.52, 593.69, 217.06],
            'data': {'description': "homemade"},
        }
    }

    client.set_frame(
        name='toward',
        pose=[966.24, 538.94, 901.63, 509.14, 792.85, 315.42],
        data={'model_type': "board"},
    )

    assert client._config.set_param.call_count == 1
    item = client._config.set_param.call_args.args[1]
    assert isinstance(item, dict)
    assert item['data'] == {'description': "homemade", 'model_type': "board"}


def test_frames_are_loaded_correctly_from_config(client):
    client._config.get_param = lambda key: {
        'mile': {
            'pose': [684.22, 729.73, 578.80, 531.12, 707.84, 277.28],
            'data': {},
        }
    }

    frames = client.frames

    assert len(frames) == 1


def test_broken_frames_are_ignored(client):
    client._config.get_param = lambda key: {
        'treat': "4Jet44",
        'outline': {
            'pose': [311.39, 999.35, 391.66, 573.02, 516.52, 917.01],
            'data': {'description': "h0sn3W91"},
        },
        'forbid': {'drawer': 574},
    }

    frames = client.frames

    assert len(frames) == 1

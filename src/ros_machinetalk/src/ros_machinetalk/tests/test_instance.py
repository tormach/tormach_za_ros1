import pytest
import rospy
from unittest.mock import MagicMock

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from ros_machinetalk.instance import InstanceClient


@pytest.fixture  # noqa: F811
def instances(mocker):  # noqa: F811
    rospy.get_param = lambda key, default=None: []
    client = InstanceClient()
    client._sub = MagicMock()
    client._add_node_srv = MagicMock()
    client._update_node_srv = MagicMock()
    client._remove_node_srv = MagicMock()
    client._config = MagicMock()
    return client


def test_when_new_node_is_added_signal_is_emit(instances):
    calls = []
    instances.on_node_added.append(lambda data: calls.append(data))

    data = [{'name': "coalhole", 'uuid': "56OA6"}]
    instances._on_config_update_received(instances._NODES_PARAM_NAME, data)

    assert len(calls) == 1
    assert calls[0] == {'name': "coalhole", 'uuid': "56OA6"}


def test_when_node_is_removed_signal_is_emit(instances):
    calls = []
    instances.on_node_removed.append(lambda data: calls.append(data))

    data = [{'name': "toluol", 'uuid': "2GSELQ5C"}]
    instances._on_config_update_received(instances._NODES_PARAM_NAME, data)
    instances._on_config_update_received(instances._NODES_PARAM_NAME, [])

    assert len(calls) == 1
    assert calls[0] == {'name': "toluol", 'uuid': "2GSELQ5C"}


def test_when_node_is_updated_signal_is_emit(instances):
    updated_calls = []
    added_calls = []
    removed_calls = []
    instances.on_node_updated.append(lambda data: updated_calls.append(data))
    instances.on_node_added.append(lambda data: added_calls.append(data))
    instances.on_node_removed.append(lambda data: removed_calls.append(data))

    data = [{'name': "deists", 'uuid': "CZRDR"}]
    instances._on_config_update_received(instances._NODES_PARAM_NAME, data)
    data = [{'name': "stylitic", 'uuid': "CZRDR"}]
    instances._on_config_update_received(instances._NODES_PARAM_NAME, data)

    assert len(updated_calls) == 1
    assert len(added_calls) == 1
    assert len(removed_calls) == 0
    assert updated_calls[0] == {'name': "stylitic", 'uuid': "CZRDR"}

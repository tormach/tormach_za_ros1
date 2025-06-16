import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_command.interfaces.machinetalk_interface import (
    MachinetalkInstanceNotFoundError,
)


@pytest.fixture  # noqa: F811
def mt_interface(mocker):  # noqa: F811
    import robot_command.interfaces.machinetalk_interface as mt

    mocker.patch.object(mt, 'InstanceClient')
    mocker.patch.object(mt, 'CommandClient')
    mocker.patch.object(mt, 'ConnectedSubscriber')
    mocker.patch.object(mt, 'StatusSubscriber')
    mt.MachinetalkInterfaceSingleton._instance = None
    return mt.MachinetalkInterfaceSingleton()


@pytest.mark.dependency()
def test_when_node_is_added_new_clients_and_subs_are_created(mt_interface):
    node = {'name': "encolden", 'uuid': "81FI"}

    mt_interface._on_node_added(node)

    assert len(mt_interface.command_clients) == 1
    assert len(mt_interface.connected_subscribers) == 1
    assert len(mt_interface.status_subscribers) == 1


@pytest.mark.dependency(
    depends=['test_when_node_is_added_new_clients_and_subs_are_created']
)
def test_when_node_is_removed_clients_and_subs_are_removed(mt_interface):
    node = {'name': "jacatoo", 'uuid': "2T7"}
    mt_interface._on_node_added(node)

    mt_interface._on_node_removed(node)

    assert len(mt_interface.command_clients) == 0
    assert len(mt_interface.connected_subscribers) == 0
    assert len(mt_interface.status_subscribers) == 0


def test_when_node_is_started_clients_and_subs_are_created(mt_interface):
    mt_interface._instance_client.nodes = [{'name': "waferer", 'uuid': "6XT8"}]
    mt_interface._add_all_nodes()

    assert len(mt_interface.command_clients) == 1
    assert len(mt_interface.connected_subscribers) == 1
    assert len(mt_interface.status_subscribers) == 1


def test_runtime_error_is_thrown_when_executing_mdi_and_instance_does_not_exist(
    mt_interface,
):
    with pytest.raises(MachinetalkInstanceNotFoundError):
        mt_interface.execute_mdi("bulge", instance="thresh")


def test_runtime_error_is_thrown_when_checking_connected_and_instance_does_not_exist(
    mt_interface,
):
    with pytest.raises(MachinetalkInstanceNotFoundError):
        mt_interface.is_connected("MBC")

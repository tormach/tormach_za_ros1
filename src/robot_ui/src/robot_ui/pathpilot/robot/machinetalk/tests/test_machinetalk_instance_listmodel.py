import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from PySide6.QtCore import QModelIndex
from PySide6.QtTest import QSignalSpy, QAbstractItemModelTester

from robot_ui.pathpilot.robot.machinetalk import MachinetalkInstanceListModel
from robot_command.interfaces import machinetalk_interface
from ros_machinetalk_msgs.msg import Instance


@pytest.fixture
def model(mocker):  # noqa: F811
    mocker.patch.object(machinetalk_interface, 'MachinetalkInterface')
    model = MachinetalkInstanceListModel()
    model._instance_client.instances = [
        Instance(
            name='esteems', uuid='7ZJNU9', host_name='127.0.0.1', version='1'
        ),
        Instance(
            name='plasmode', uuid='1M4P', host_name="127.0.1.1", version='627'
        ),
    ]
    model._instance_client.nodes = [{'name': 'razoo', 'uuid': '1M4P'}]
    model._interface.is_connected.return_value = False
    model._update_model()
    return model


def test_creating_model_from_instances_and_nodes_works(model):
    assert model.rowCount(QModelIndex()) == 2
    assert model.columnCount(QModelIndex()) == 6
    index = model.index(0, 0, QModelIndex())
    assert model.data(index, model.Roles.NameRole) == 'razoo'
    assert model.data(index, model.Roles.UuidRole) == '1M4P'
    assert model.data(index, model.Roles.HostNameRole) == '127.0.1.1'
    assert model.data(index, model.Roles.VersionRole) == '627'
    assert model.data(index, model.Roles.SelectedRole) is True
    index = model.index(1, 0, QModelIndex())
    assert model.data(index, model.Roles.NameRole) == 'esteems'
    assert model.data(index, model.Roles.UuidRole) == '7ZJNU9'
    assert model.data(index, model.Roles.SelectedRole) is False


def test_when_instances_are_changed_model_is_updated(model):
    spy = QSignalSpy(model.modelReset)

    model._instance_client.instances = [
        Instance(
            name='kunk', uuid='1YO0ZOQ', host_name='192.168.0.1', version='724'
        )
    ]
    model._instance_client.nodes = []
    model._update_model()

    assert spy.count() == 1
    assert model.rowCount(QModelIndex()) == 1
    index = model.index(0, 0, QModelIndex())
    assert model.data(index, model.Roles.NameRole) == 'kunk'


def test_when_nodes_are_changed_model_is_update(model):
    spy = QSignalSpy(model.modelReset)

    model._instance_client.nodes = []
    model._update_model()

    assert spy.count() == 1
    assert model.rowCount(QModelIndex()) == 2
    index = model.index(1, 0, QModelIndex())
    assert model.data(index, model.Roles.SelectedRole) is False


def test_model_data_is_updated_when_connected_changes(model):
    spy = QSignalSpy(model.dataChanged)

    model._on_connected_changed(True, "1M4P")

    assert spy.count() == 1
    assert spy.at(0)[0] == model.index(0, 0)  # row 0
    assert spy.at(0)[1] == model.index(0, 0)  # row 0


def test_machinetalk_instance_model_implementation(model):
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )

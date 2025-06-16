import pytest

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtTest import QAbstractItemModelTester


from robot_ui.pathpilot.logging import MessageDataModel
from robot_ui.pathpilot.logging.logging import LogSeverityLevel
from robot_ui.pathpilot.logging.message import Message


@pytest.fixture
def messages():
    new_message = Message()
    new_message.message = 'sabred'
    new_message.severity = LogSeverityLevel.Debug
    new_message.topics = ['sturgeon']
    msgs = [new_message]
    new_message = Message()
    new_message.message = 'formers'
    new_message.severity = LogSeverityLevel.Info
    new_message.topics = ['sturgeon']
    msgs.append(new_message)
    new_message = Message()
    new_message.message = 'neophron'
    new_message.severity = LogSeverityLevel.Fatal
    new_message.topics = ['aloysius']
    msgs.append(new_message)
    return msgs


@pytest.mark.dependency()
def test_message_data_model_can_be_filled_with_messages(messages):
    model = MessageDataModel()
    model.insert_rows(messages)

    assert model.rowCount() == 3
    index = model.index(2, 0, QModelIndex())
    assert model.data(index, model.Roles.SeverityRole) == LogSeverityLevel.Debug
    assert model.data(index, model.Roles.MessageRole) == 'sabred'
    assert model.data(index, model.Roles.TopicsRole) == ['sturgeon']
    index = model.index(
        2,
        model.Roles.SeverityRole - model.Roles.FirstDataRole - 1,
        QModelIndex(),
    )
    assert model.data(index, Qt.DisplayRole) == 'Debug'
    index = model.index(1, 0, QModelIndex())
    assert model.data(index, model.Roles.SeverityRole) == LogSeverityLevel.Info
    assert model.data(index, model.Roles.MessageRole) == 'formers'
    assert model.data(index, model.Roles.TopicsRole) == ['sturgeon']
    index = model.index(0, 0, QModelIndex())
    assert model.data(index, model.Roles.SeverityRole) == LogSeverityLevel.Fatal
    assert model.data(index, model.Roles.MessageRole) == 'neophron'
    assert model.data(index, model.Roles.TopicsRole) == ['aloysius']


def test_message_limit_is_enforced(messages):
    model = MessageDataModel()

    model.messageLimit = 2
    model.insert_rows(messages)

    assert model.rowCount() == 2
    index = model.index(1, 0, QModelIndex())
    assert model.data(index, model.Roles.MessageRole) == 'formers'
    index = model.index(0, 0, QModelIndex())
    assert model.data(index, model.Roles.MessageRole) == 'neophron'


def test_highest_severity_matches_highest_severity_in_messages(messages):
    model = MessageDataModel()

    model.insert_rows(messages)

    assert model.highestSeverity == LogSeverityLevel.Fatal


def test_highest_severity_is_reset_with_model(messages):
    model = MessageDataModel()
    model.insert_rows(messages)

    model.removeAll()

    assert model.highestSeverity == LogSeverityLevel.Debug


def test_message_data_model_implementation(messages):
    model = MessageDataModel()
    model.insert_rows(messages)
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )

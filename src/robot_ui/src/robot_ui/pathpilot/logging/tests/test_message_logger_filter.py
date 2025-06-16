import pytest
from rosgraph_msgs.msg import Log

from robot_ui.pathpilot.logging import MessageLoggerFilter


@pytest.fixture
def messages():
    msg = Log()
    msg.msg = "Something went wrong"

    msg.level = Log.ERROR
    msg.name = "/robot_ui"
    all_ = [msg]
    msg = Log()
    msg.msg = "This is an info"
    msg.level = Log.INFO
    msg.name = "/program_interpreter"
    all_.append(msg)
    return all_


def test_message_is_filtered_out_if_not_in_nodes(messages):
    filter_ = MessageLoggerFilter()
    filter_.nodes = ["/robot_ui"]

    filtered = [
        message for message in messages if filter_.filter_message(message)
    ]

    assert len(filtered) == 1
    assert filtered[0].name == "/robot_ui"


def test_message_is_filtered_out_when_severity_is_below_threshold(messages):
    filter_ = MessageLoggerFilter()
    filter_.severityThreshold = Log.ERROR

    filtered = [
        message for message in messages if filter_.filter_message(message)
    ]

    assert len(filtered) == 1
    assert filtered[0].level == Log.ERROR

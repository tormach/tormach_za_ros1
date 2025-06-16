from unittest.mock import MagicMock

from ros_machinetalk.connected import ConnectedPublisher


def test_publisher_publishes_disconnected_when_started():
    conn = ConnectedPublisher([])
    conn._pub = MagicMock()

    conn.start()

    assert conn._pub.publish.call_count == 1


def test_publisher_publishes_connected_when_all_services_are_connected():
    conn = ConnectedPublisher(["intagli", "cystoma"])
    conn._pub = MagicMock()
    conn.start()

    conn.set_status(True, "intagli")
    conn.set_status(True, "cystoma")

    assert conn._pub.publish.call_count == 3
    assert conn._pub.publish.mock_calls[2][1][0] is True


def test_publisher_publishes_disconnected_when_service_is_disconnected():
    conn = ConnectedPublisher(["mesarch"])
    conn._pub = MagicMock()
    conn.start()

    conn.set_status(True, "mesarch")
    conn.set_status(False, "mesarch")

    assert conn._pub.publish.call_count == 3
    assert conn._pub.publish.mock_calls[2][1][0] is False

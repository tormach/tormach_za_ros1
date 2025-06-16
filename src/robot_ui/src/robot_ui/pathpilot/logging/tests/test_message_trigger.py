from unittest import mock

import rospy
from robot_ui.pathpilot.logging import MessageTrigger


def test_logger_subscribes_to_topics_when_ready():
    logger = MessageTrigger()

    logger.topics = ['topic1', 'topic2']
    logger.ready = True

    assert sorted(logger._subscribers.keys()) == ['topic1', 'topic2']


@mock.patch.object(rospy.Subscriber, 'unregister')
@mock.patch.object(rospy, 'Subscriber')
def test_logger_updates_subscription_correctly(
    stub_subscriber, stub_unregister
):
    logger = MessageTrigger()

    logger.ready = True
    logger.topics = ['foo', 'bar']

    assert sorted(logger._subscribers.keys()) == ['bar', 'foo']
    assert len(stub_unregister.mock_calls) == 1

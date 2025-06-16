import rospy
import unique_id

from robot_command_msgs.msg import NotificationMessage, AcknowledgeNotification

NOTIFICATION_MESSAGES_TOPIC = 'robot_command/notification_messages'
ALERT_MESSAGES_TOPIC = 'robot_command/alert_messages'
ACKNOWLEDGE_NOTIFICATION_TOPIC = 'robot_command/acknowledge_notification'


class NotificationResponse:
    NONE = 0
    OK = 1
    ABORT = 2


class NotificationInterface:
    def __init__(self):
        self._identifier = unique_id.fromRandom()
        rospy.loginfo(
            f'created a NotificationInterface with identifier {self._identifier}'
        )
        topic = NOTIFICATION_MESSAGES_TOPIC
        rospy.logdebug(f'creating publisher for {topic}')
        self._notification_messages_pub = rospy.Publisher(
            topic, NotificationMessage, queue_size=1
        )
        topic = ALERT_MESSAGES_TOPIC
        rospy.logdebug(f'creating publisher for {topic}')
        self._alert_messages_pub = rospy.Publisher(
            topic, NotificationMessage, queue_size=1, latch=True
        )
        topic = ACKNOWLEDGE_NOTIFICATION_TOPIC
        rospy.logdebug(
            'creating acknowledge notification subscriber for {topic}'
        )
        self._user_acknowledgement_sub = rospy.Subscriber(
            topic,
            AcknowledgeNotification,
            self._on_user_acknowledgement_notification_received,
        )
        self._message_response = NotificationResponse.NONE
        self._user_input = None
        self._message_in_progress = False

    @property
    def message_active(self):
        return self._message_in_progress

    @property
    def message_response(self):
        return self._message_response

    @property
    def user_input(self):
        return self._user_input

    def shutdown(self) -> None:
        # self._notification_messages_pub.unregister()
        # self._alert_messages_pub.unregister()
        self._user_acknowledgement_sub.unregister()

    def deactivate_message(self) -> None:
        msg = NotificationMessage(
            identifier=unique_id.toMsg(self._identifier), active=False
        )
        self._alert_messages_pub.publish(msg)

    def notification_message(self, message: str, image_path='') -> None:
        msg = NotificationMessage(
            identifier=unique_id.toMsg(self._identifier),
            type=NotificationMessage.TYPE_NOTIFICATION,
            message=message,
            image_path=image_path,
            active=True,
        )
        self._notification_messages_pub.publish(msg)
        self._message_response = NotificationResponse.NONE
        rospy.loginfo(message)

    def warning_message(self, message: str, image_path='') -> None:
        msg = NotificationMessage(
            identifier=unique_id.toMsg(self._identifier),
            type=NotificationMessage.TYPE_WARNING,
            message=message,
            image_path=image_path,
            active=True,
        )
        self._alert_messages_pub.publish(msg)
        self._message_response = NotificationResponse.NONE
        self._message_in_progress = True
        rospy.logwarn(message)

    def error_message(self, message: str, image_path='') -> None:
        msg = NotificationMessage(
            identifier=unique_id.toMsg(self._identifier),
            type=NotificationMessage.TYPE_ERROR,
            message=message,
            image_path=image_path,
            active=True,
        )
        self._alert_messages_pub.publish(msg)
        self._message_response = NotificationResponse.NONE
        self._message_in_progress = True
        rospy.logerr(message)

    def user_input_message(
        self, message: str, image_path='', default=''
    ) -> None:
        msg = NotificationMessage(
            identifier=unique_id.toMsg(self._identifier),
            type=NotificationMessage.TYPE_USER_INPUT,
            message=message,
            image_path=image_path,
            active=True,
            default=default,
        )
        self._alert_messages_pub.publish(msg)
        self._message_response = NotificationResponse.NONE
        self._user_input = None
        self._message_in_progress = True

    def _on_user_acknowledgement_notification_received(
        self, msg: AcknowledgeNotification
    ) -> None:
        # Message is not targeted at this Interface
        if unique_id.fromMsg(msg.identifier) != self._identifier:
            return
        if msg.response == AcknowledgeNotification.RESPONSE_OK:
            self._message_response = NotificationResponse.OK
            self._user_input = msg.user_input
        elif msg.response == AcknowledgeNotification.RESPONSE_ABORT:
            self._message_response = NotificationResponse.ABORT
            self._user_input = None
        self._message_in_progress = False


class NotificationInterfaceSingleton:
    """
    Singleton interface class to notifications
    """

    _instance = None

    def __init__(self):
        if not NotificationInterfaceSingleton._instance:
            NotificationInterfaceSingleton._instance = NotificationInterface()

    def __getattr__(self, item):
        return getattr(self._instance, item)

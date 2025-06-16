from PySide6.QtCore import QObject, Property, Signal, Slot, QEnum
from PySide6.QtQml import QmlElement, QmlUncreatable

import uuid as uuid_lib
import unique_id
from collections import deque

import rospy
from robot_command_msgs.msg import NotificationMessage as RosNotificationMessage
from robot_command_msgs.msg import (
    AcknowledgeNotification as RosAcknowledgeNotification,
)

from robot_command.program_blocks.notify_block import NotifyType

from ....qt_helpers import MultiSlot, ensure_cleanup


NOTIFICATION_MESSAGES_TOPIC = 'robot_command/notification_messages'
ALERT_MESSAGES_TOPIC = 'robot_command/alert_messages'
ACKNOWLEDGE_NOTIFICATION_TOPIC = 'robot_command/acknowledge_notification'

QML_IMPORT_NAME = 'pathpilot.robot.program.notification'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class NotificationMessageModel:
    def __init__(
        self,
        uuid,
        image_path="",
        message_text="",
        message_type=NotifyType.Notification,
        default="",
    ):
        self._uuid = uuid
        self._image_path = image_path
        self._message_text = message_text
        self._message_type = message_type
        self._default = default

    @property
    def uuid(self):
        return self._uuid

    @property
    def image_path(self):
        return self._image_path

    @property
    def message_text(self):
        return self._message_text

    @property
    def message_type(self):
        return self._message_type

    @property
    def default(self):
        return self._default


@QmlElement
@QmlUncreatable("NotificationMessage is not creatable in QML")
class NotificationMessage(QObject):
    """
    Notification message for the ProgramNotifications Controller
    """

    QEnum(NotifyType)

    activeChanged = Signal(bool)
    messageChanged = Signal(str)
    imagePathChanged = Signal(str)
    typeChanged = Signal(int)
    defaultChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._active_message_model = None

    @property
    def model(self):
        return (
            self._active_message_model
            if self._active_message_model is not None
            else None
        )

    @model.setter
    def model(self, message_model: NotificationMessageModel):
        if self._active_message_model is not message_model:
            self._active_message_model = message_model
            self.messageChanged.emit(self.message)
            self.imagePathChanged.emit(self.imagePath)
            self.typeChanged.emit(self.type)
            self.defaultChanged.emit(self.default)
            self.activeChanged.emit(self.active)

    @Property(bool, notify=activeChanged)
    def active(self):
        return self.model is not None

    @Property(str, notify=messageChanged)
    def message(self):
        return self.model.message_text if self.model is not None else ""

    @Property(str, notify=imagePathChanged)
    def imagePath(self):
        return self.model.image_path if self.model is not None else ""

    @Property(int, notify=typeChanged)
    def type(self):
        return (
            self.model.message_type
            if self.model is not None
            else NotifyType.Notification
        )

    @Property(str, notify=defaultChanged)
    def default(self):
        return self.model.default if self.model is not None else ""


@QmlElement
class ProgramNotifications(QObject):
    """
    Program notifications are created by NotificationInterface to prompt
    the user for input.
    """

    messageReceived = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._message = NotificationMessage()
        self._alert_message = NotificationMessage()

        self._messages = deque()
        self._alert_messages = deque()

        self._sub = rospy.Subscriber(
            NOTIFICATION_MESSAGES_TOPIC,
            RosNotificationMessage,
            self._on_notification_message_received,
        )
        self._alert_sub = rospy.Subscriber(
            ALERT_MESSAGES_TOPIC,
            RosNotificationMessage,
            self._on_alert_message_received,
        )

        self._acknowledge_notification_pub = rospy.Publisher(
            ACKNOWLEDGE_NOTIFICATION_TOPIC,
            RosAcknowledgeNotification,
            queue_size=10,
        )

        ensure_cleanup(self._shutdown)

    def pick_and_display(self) -> None:
        if self._alert_message.active or self._message.active:
            return

        if self._alert_messages:
            message = self._alert_messages.pop()
            self._alert_message.model = message
            return

        if self._messages:
            message = self._messages.pop()
            self._message.model = message

    def deactivate_and_remove(self, uuid: uuid_lib.UUID) -> None:
        # Check if the message is currently active
        if (
            self._alert_message.active
            and self._alert_message.model.uuid == uuid
        ):
            self.notificationClosed(self._alert_message)
            return
        # Shown Notification messages cannot be deactivated

        for item in self._alert_messages:
            if item.uuid == uuid:
                self._alert_messages.remove(item)
                return

        for item in self._messages:
            if item.uuid == uuid:
                self._messages.remove(item)
        # It's some unknown message or error, either way we don't care

    def _on_notification_message_received(
        self, msg: RosNotificationMessage
    ) -> None:
        uuid = unique_id.fromMsg(msg.identifier)
        rospy.logdebug(f'Received notification message from {uuid}')

        # Test if user wants to delete the message from stack of as of yet
        # unshown messages
        if not msg.active:
            self.deactivate_and_remove(uuid)
            return

        new_message = NotificationMessageModel(
            uuid=uuid,
            message_text=msg.message,
            image_path=msg.image_path,
            message_type=msg.type,
            default=msg.default,
        )

        self._messages.append(new_message)
        self.pick_and_display()

        self.messageReceived.emit()

    def _on_alert_message_received(self, msg: RosNotificationMessage) -> None:
        uuid = unique_id.fromMsg(msg.identifier)
        rospy.logdebug(f'Received alert message from {uuid}')

        # Test if user wants to delete the message
        if not msg.active:
            self.deactivate_and_remove(uuid)
            return

        new_message = NotificationMessageModel(
            uuid=uuid,
            message_text=msg.message,
            image_path=msg.image_path,
            message_type=msg.type,
            default=msg.default,
        )

        # Wanted changes are on active message
        if (
            self._alert_message.active
            and self._alert_message.model.uuid == uuid
        ):
            self._alert_message.model = new_message
            return

        # Check if message with uuid is in queue
        for item in self._alert_messages:
            if item.uuid == uuid:
                self._alert_messages.remove(item)
                break

        self._alert_messages.append(new_message)
        self.pick_and_display()

    @Property(NotificationMessage, constant=True)
    def message(self):
        return self._message

    @Property(NotificationMessage, constant=True)
    def alertMessage(self):
        return self._alert_message

    @Slot(NotificationMessage)
    def notificationClosed(
        self, notification_message: NotificationMessage
    ) -> None:
        rospy.logdebug(
            f"Notification from {notification_message.model.uuid} was closed."
        )
        notification_message.model = None
        self.pick_and_display()

    @MultiSlot([None, str])
    def accept(self, default="") -> None:
        self._acknowledge_notification_pub.publish(
            RosAcknowledgeNotification(
                unique_id.toMsg(self._alert_message.model.uuid),
                RosAcknowledgeNotification.RESPONSE_OK,
                default,
            )
        )

    @Slot()
    def abort(self) -> None:
        self._acknowledge_notification_pub.publish(
            RosAcknowledgeNotification(
                unique_id.toMsg(self._alert_message.model.uuid),
                RosAcknowledgeNotification.RESPONSE_ABORT,
                "",
            )
        )

    @Slot()
    def _shutdown(self):
        self._sub.unregister()
        self._alert_sub.unregister()
        self._acknowledge_notification_pub.unregister()

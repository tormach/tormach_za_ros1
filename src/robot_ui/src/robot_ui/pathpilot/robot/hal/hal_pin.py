from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtQml import QPyQmlParserStatus, QmlElement

import rospy
from std_msgs.msg import Bool, Float64, Int32, UInt32

from ...qt_helpers import ensure_cleanup
from .hal_types import PinDirection, PinType

QML_IMPORT_NAME = 'pathpilot.robot.hal'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class HalPin(QPyQmlParserStatus):
    """
    This class represents a HAL pin exposed via hal_io in QML.
    """

    nameChanged = Signal(str)
    typeChanged = Signal(int)
    directionChanged = Signal(int)
    syncedChanged = Signal(bool)
    enabledChanged = Signal(bool)
    topicChanged = Signal(str)
    valueChanged = Signal('QVariant')

    _MSG_TYPE_MAP = {
        PinType.Bit: Bool,
        PinType.Float: Float64,
        PinType.S32: Int32,
        PinType.U32: UInt32,
    }

    def __init__(
        self,
        parent=None,
        name='',
        topic='',
        type_=PinType.Bit,
        direction=PinDirection.In,
        enabled=True,
        synced=False,
        value=False,
    ):
        super().__init__(parent)

        self._name = name
        self._topic = topic
        self._type = type_
        self._direction = direction
        self._enabled = enabled
        self._synced = synced
        self._value = value

        self._sub = None
        self._pub = None
        self._remote_update = False

        self.enabledChanged.connect(self._on_enabled_changed)
        ensure_cleanup(self._stop)

    def classBegin(self):
        pass

    def componentComplete(self):
        if self._enabled and not self._sub:
            self._start()

    @Slot(bool)
    def _on_enabled_changed(self, enabled):
        if enabled:
            self._start()
        else:
            self._stop()

    def _start(self):
        if self._topic == '':
            return

        self._synced = False
        self._sub = rospy.Subscriber(
            self._topic,
            self._MSG_TYPE_MAP[self._type],
            self._on_message_received,
        )
        if self._direction in (PinDirection.IO, PinDirection.Out):
            self._pub = rospy.Publisher(
                self._topic, self._MSG_TYPE_MAP[self._type], queue_size=1
            )
        self.syncedChanged.emit(self._synced)

    @Slot()
    def _stop(self):
        if self._sub:
            self._sub.unregister()
            self._sub = None
        if self._pub:
            # self._pub.unregister()  # see https://github.com/ros/ros_comm/issues/111
            self._pub = None

    def _on_message_received(self, msg):
        self._value = msg.data
        self._synced = True
        self.valueChanged.emit(self._value)
        self.syncedChanged.emit(self._synced)

    def _publish_update(self, value):
        if not self._pub:
            return
        self._synced = False
        self.syncedChanged.emit(self._synced)
        self._pub.publish(value)

    @Property('QVariant', notify=valueChanged)
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == self._value:
            return
        self._value = value
        self.valueChanged.emit(value)
        self._publish_update(value)

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == self._name:
            return
        self._name = value
        self.nameChanged.emit(value)

    @Property(int, notify=typeChanged)
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value == self._type:
            return
        self._type = PinType(value)
        self.typeChanged.emit(value)

    @Property(int, notify=directionChanged)
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        if value == self._direction:
            return
        self._direction = PinDirection(value)
        self.directionChanged.emit(value)

    @Property(str, notify=topicChanged)
    def topic(self):
        return self._topic

    @topic.setter
    def topic(self, value):
        if value == self._topic:
            return
        self._topic = value
        self.topicChanged.emit(value)

    @Property(bool, notify=enabledChanged)
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if value == self._enabled:
            return
        self._enabled = value
        self.enabledChanged.emit(value)

    @Property(bool, notify=syncedChanged)
    def synced(self):
        return self._synced

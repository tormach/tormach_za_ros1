from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement
from rosgraph_msgs.msg import Log
from rospy import Subscriber

from ..qt_helpers import ensure_cleanup
from .logging import LogSeverityLevel
from .message_logger_filter import MessageLoggerFilter

QML_IMPORT_NAME = 'pathpilot.logging'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class MessageTrigger(QObject):
    topicsChanged = Signal('QStringList')
    triggeredChanged = Signal(bool)
    severityThresholdChanged = Signal(int)
    readyChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._topics = {'rosout_agg'}
        self._subscribers = {}
        self._triggered = False
        self._ready = False
        self._severity_threshold = LogSeverityLevel.Error
        self._filter = MessageLoggerFilter()

        self.readyChanged.connect(self._update_subscriptions)
        self.topicsChanged.connect(self._update_subscriptions)
        ensure_cleanup(self._shutdown)

    @Property('QStringList', notify=topicsChanged)
    def topics(self):
        return list(self._topics)

    @topics.setter
    def topics(self, value):
        if value == list(self._topics):
            return
        self._topics = set(value)
        self.topicsChanged.emit(value)

    @Property(bool, notify=readyChanged)
    def ready(self):
        return self._ready

    @ready.setter
    def ready(self, value):
        if value == self._ready:
            return
        self._ready = value
        self.readyChanged.emit(value)

    @Property(bool, notify=triggeredChanged)
    def triggered(self):
        return self._triggered

    @Property(MessageLoggerFilter, constant=True)
    def filter(self):
        return self._filter

    @Slot()
    def reset(self):
        self._triggered = False
        self.triggeredChanged.emit(False)

    @Slot()
    def _update_subscriptions(self):
        old_topics = set(self._subscribers.keys())
        if self._ready:
            must_subscribe = self._topics - old_topics
            must_unsubscribe = old_topics - self._topics
        else:
            must_subscribe = set()
            must_unsubscribe = old_topics

        for topic in must_unsubscribe:
            sub = self._subscribers[topic]
            sub.unregister()
            del self._subscribers[topic]

        for topic in must_subscribe:
            sub = Subscriber(topic, Log, self._on_message_received)
            self._subscribers[topic] = sub

    @Slot()
    def _shutdown(self):
        self._topics = set()
        self._update_subscriptions()

    def _on_message_received(self, log_msg):
        if self._triggered:
            return
        if self._filter.filter_message(log_msg):
            self._triggered = True
            self.triggeredChanged.emit(self._triggered)

from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    Slot,
    QMutex,
    QTimer,
    QMutexLocker,
)
from PySide6.QtQml import QmlElement
from rosgraph_msgs.msg import Log
from rospy import Subscriber

from ..qt_helpers import ensure_cleanup
from .logging import Logging
from .message_logger_filter import MessageLoggerFilter
from .message_data_model import MessageDataModel

MESSAGE_FLUSH_INTERVAL_MS = 100


QML_IMPORT_NAME = 'pathpilot.logging'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class MessageLogger(QObject):
    modelChanged = Signal(MessageDataModel)
    topicsChanged = Signal('QStringList')
    readyChanged = Signal(bool)
    pausedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None
        self._topics = {'rosout_agg'}
        self._subscribers = {}
        self._ready = False
        self._paused = False
        self._filter = MessageLoggerFilter()

        # queue to store incoming data which get flushed periodically to the model
        # required since QSortProxyModel can not handle a high insert rate
        self._message_queue = []
        self._mutex = QMutex()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._flush_messages)

        self.readyChanged.connect(self._update_subscriptions)
        self.readyChanged.connect(self._start_stop_timer)
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

    @Property(MessageDataModel, notify=modelChanged)
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if value == self._model:
            return
        self._model = value
        self.modelChanged.emit(value)

    @Property(bool, notify=readyChanged)
    def ready(self):
        return self._ready

    @ready.setter
    def ready(self, value):
        if value == self._ready:
            return
        self._ready = value
        self.readyChanged.emit(value)

    @Property(bool, notify=pausedChanged)
    def paused(self):
        return self._paused

    @paused.setter
    def paused(self, value):
        if value == self._paused:
            return
        self._paused = value
        self.pausedChanged.emit(value)

    @Property(MessageLoggerFilter, constant=True)
    def filter(self):
        return self._filter

    @Slot()
    def _start_stop_timer(self):
        if self._ready:
            self._timer.start(MESSAGE_FLUSH_INTERVAL_MS)
        else:
            self._timer.stop()

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
            sub = Subscriber(topic, Log, self._queue_message)
            self._subscribers[topic] = sub

    @Slot()
    def _shutdown(self):
        self._topics = set()
        self._update_subscriptions()
        self._ready = False
        self._start_stop_timer()

    def _queue_message(self, log_msg: Log):
        if self._paused:
            return
        if not self._filter.filter_message(log_msg):
            return
        msg = Logging.convert_rosgraph_log_message(log_msg)
        with QMutexLocker(self._mutex):
            self._message_queue.append(msg)

    @Slot()
    def _flush_messages(self):
        with QMutexLocker(self._mutex):
            msgs, self._message_queue = self._message_queue, []

        if self._model and msgs:
            self._model.insert_rows(msgs)

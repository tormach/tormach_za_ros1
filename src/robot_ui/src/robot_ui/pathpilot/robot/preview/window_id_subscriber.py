from PySide6.QtCore import Signal, Property, Slot, QObject
from PySide6.QtQml import QmlElement

import rospy
from std_msgs.msg import UInt32

from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.preview'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WindowIdSubscriber(QObject):
    winIdChanged = Signal()
    topicChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._win_id = 0
        self._topic = ""
        self._sub = None

        ensure_cleanup(self._unsubscribe)

    def _subscribe(self):
        if self._sub is None and self._topic:
            self._sub = rospy.Subscriber(self._topic, UInt32, self._on_win_id)

    @Slot()
    def _unsubscribe(self):
        if self._sub is not None:
            self._sub.unregister()
            self._sub = None

    @Property(str, notify=topicChanged)
    def topic(self):
        return self._topic

    @topic.setter
    def topic(self, value):
        if value == self._topic:
            return

        self._unsubscribe()

        self._topic = value
        self.topicChanged.emit()

        self._subscribe()

    @Property(int, notify=winIdChanged)
    def winId(self):
        return self._win_id

    def _set_win_id(self, value):
        if value == self._win_id:
            return

        self._win_id = value
        self.winIdChanged.emit()

    def _on_win_id(self, msg):
        self._set_win_id(msg.data)

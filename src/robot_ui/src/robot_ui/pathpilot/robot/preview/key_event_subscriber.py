from PySide6.QtCore import Signal, Property, Slot, QObject, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtQml import QmlElement

import rospy
from rviz.msg import KeyEvent

from ...core import GlobalShortcuts
from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.preview'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class KeyEventSubscriber(QObject):
    globalShortcutsChanged = Signal(GlobalShortcuts)
    topicChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._topic = ""
        self._sub = None
        self._global_shortcuts = None

        ensure_cleanup(self._unsubscribe)

    def _subscribe(self):
        if self._sub is None and self._topic:
            self._sub = rospy.Subscriber(
                self._topic, KeyEvent, self._on_key_event
            )

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

    @Property(GlobalShortcuts, notify=globalShortcutsChanged)
    def globalShortcuts(self):
        return self._global_shortcuts

    @globalShortcuts.setter
    def globalShortcuts(self, value):
        if value == self._global_shortcuts:
            return

        self._global_shortcuts = value
        self.globalShortcutsChanged.emit(value)

    def _on_key_event(self, msg: KeyEvent):
        if self._global_shortcuts is None:
            return

        event = QKeyEvent(
            QEvent.Type(msg.event_type),
            msg.key,
            Qt.KeyboardModifier(msg.modifiers),
        )
        self._global_shortcuts.eventFilter(self, event)

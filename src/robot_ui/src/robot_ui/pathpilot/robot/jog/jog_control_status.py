from enum import IntEnum
import rospy
from PySide6.QtCore import Property, Signal, Slot, QObject, QEnum
from PySide6.QtQml import QmlElement
from std_msgs.msg import Int8

from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class StatusCodes(IntEnum):
    InvalidStatus = -1
    NoWarningStatus = 0
    DecelerateForSingularityStatus = 1
    HaltForSingularityStatus = 2
    DecelerateForCollisionStatus = 3
    HaltForCollisionStatus = 4
    JointBoundStatus = 5


@QmlElement
class JogControlStatus(QObject):
    GUI_JOG_STATUS_TOPIC = 'jog_arm_server/status'
    JOY_JOG_STATUS_TOPIC = 'jog_arm_server/status_joy'

    QEnum(StatusCodes)

    guiStatusChanged = Signal(int)
    joyStatusChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._gui_status = StatusCodes.InvalidStatus
        self._joy_status = StatusCodes.InvalidStatus

        self._subs = [
            rospy.Subscriber(
                self.GUI_JOG_STATUS_TOPIC,
                Int8,
                self._on_gui_status_message_received,
            ),
            rospy.Subscriber(
                self.JOY_JOG_STATUS_TOPIC,
                Int8,
                self._on_joy_status_message_received,
            ),
        ]
        ensure_cleanup(self._shutdown)

    @Slot()
    def _shutdown(self):
        for sub in self._subs:
            sub.unregister()

    def _on_gui_status_message_received(self, msg):
        if msg.data is not self._gui_status:
            self._gui_status = StatusCodes(msg.data)
            self.guiStatusChanged.emit(msg.data)

    def _on_joy_status_message_received(self, msg):
        if msg.data is not self._joy_status:
            self._joy_status = StatusCodes(msg.data)
            self.joyStatusChanged.emit(msg.data)

    @Property(int, notify=guiStatusChanged)
    def guiStatus(self):
        return self._gui_status

    @Property(int, notify=joyStatusChanged)
    def joyStatus(self):
        return self._joy_status

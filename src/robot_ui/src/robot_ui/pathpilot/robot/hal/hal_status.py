from rospy import Subscriber
from std_msgs.msg import Bool

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement

from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.hal'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class HalStatus(QObject):
    """
    Monitors the status of the HAL config via the HalMgr ready topic.
    """

    READY_TOPIC = '/hal_mgr/ready'
    readyChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._ready = False

        self._sub = Subscriber(
            self.READY_TOPIC, Bool, self._on_message_received
        )
        ensure_cleanup(self._shutdown)

    @Property(bool, notify=readyChanged)
    def ready(self):
        return self._ready

    def _on_message_received(self, msg):
        ready = msg.data
        if ready is not self._ready:
            self._ready = ready
            self.readyChanged.emit(ready)

    @Slot()
    def _shutdown(self):
        self._sub.unregister()

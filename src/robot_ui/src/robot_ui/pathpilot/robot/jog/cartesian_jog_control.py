from PySide6.QtCore import Property, Signal, Slot, QObject, QTimer
from PySide6.QtQml import QmlElement

import rospy
from geometry_msgs.msg import TwistStamped

from ...qt_helpers import ensure_cleanup

DEFAULT_AUTOREPEAT_INTERVAL = 250

JOG_COMMAND_TOPIC = 'jog_arm_server/frame_delta_jog_cmds'

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CartesianJogControl(QObject):
    xChanged = Signal(float)
    yChanged = Signal(float)
    zChanged = Signal(float)
    rxChanged = Signal(float)
    ryChanged = Signal(float)
    rzChanged = Signal(float)
    frameIdChanged = Signal(str)
    autorepeatIntervalChanged = Signal(int)
    enabledChanged = Signal(bool)
    activeChanged = Signal(bool)

    def __init__(
        self,
        parent=None,
        enabled=False,
        x=0.0,
        y=0.0,
        z=0.0,
        rx=0.0,
        ry=0.0,
        rz=0.0,
        frame_id="",
        autorepeat_interval=DEFAULT_AUTOREPEAT_INTERVAL,
    ):
        super().__init__(parent)

        self._x = x
        self._y = y
        self._z = z
        self._rx = rx
        self._ry = ry
        self._rz = rz
        self._frame_id = frame_id
        self._autorepeat_interval = autorepeat_interval
        self._timer = None
        self._enabled = enabled
        self._all_zeros = True
        self._all_zeros_published = False

        self._pub = rospy.Publisher(
            JOG_COMMAND_TOPIC, TwistStamped, queue_size=1
        )

        self.autorepeatIntervalChanged.connect(self._update_timer)
        self.enabledChanged.connect(self._update_timer)
        # reset update timer when values change
        self.xChanged.connect(self._update_all_zeros)
        self.xChanged.connect(self._update_timer)
        self.yChanged.connect(self._update_all_zeros)
        self.yChanged.connect(self._update_timer)
        self.zChanged.connect(self._update_all_zeros)
        self.zChanged.connect(self._update_timer)
        self.rxChanged.connect(self._update_all_zeros)
        self.rxChanged.connect(self._update_timer)
        self.ryChanged.connect(self._update_all_zeros)
        self.ryChanged.connect(self._update_timer)
        self.rzChanged.connect(self._update_all_zeros)
        self.rzChanged.connect(self._update_timer)

        ensure_cleanup(self._shutdown)

    @Slot()
    def _update_timer(self):
        if self._timer:
            self._timer.stop()
            self._timer = None
        if not self._enabled:
            return
        if self._autorepeat_interval > 0:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._publish_status)
            self._timer.setInterval(self._autorepeat_interval)
            self._timer.start()
        self._publish_status()

    @Slot()
    def _publish_status(self):
        if self._all_zeros and self._all_zeros_published:
            return
        ts = TwistStamped()
        ts.header.stamp = rospy.Time.now()
        ts.header.frame_id = self._frame_id
        ts.twist.linear.x = self._x
        ts.twist.linear.y = self._y
        ts.twist.linear.z = self._z
        ts.twist.angular.x = self._rx
        ts.twist.angular.y = self._ry
        ts.twist.angular.z = self._rz
        self._pub.publish(ts)
        self._all_zeros_published = True

    @Property(float, notify=xChanged)
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        if value == self._x:
            return
        self._x = value
        self.xChanged.emit(value)

    @Property(float, notify=yChanged)
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        if value == self._y:
            return
        self._y = value
        self.yChanged.emit(value)

    @Property(float, notify=zChanged)
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        if value == self._z:
            return
        self._z = value
        self.zChanged.emit(value)

    @Property(float, notify=rxChanged)
    def rx(self):
        return self._rx

    @rx.setter
    def rx(self, value):
        if value == self._rx:
            return
        self._rx = value
        self.rxChanged.emit(value)

    @Property(float, notify=ryChanged)
    def ry(self):
        return self._ry

    @ry.setter
    def ry(self, value):
        if value == self._ry:
            return
        self._ry = value
        self.ryChanged.emit(value)

    @Property(float, notify=rzChanged)
    def rz(self):
        return self._rz

    @rz.setter
    def rz(self, value):
        if value == self._rz:
            return
        self._rz = value
        self.rzChanged.emit(value)

    @Property(str, notify=frameIdChanged)
    def frameId(self):
        return self._frame_id

    @frameId.setter
    def frameId(self, value):
        if value == self._frame_id:
            return
        self._frame_id = value
        self.frameIdChanged.emit(value)

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._enabled and not self._all_zeros

    @Slot()
    def _update_all_zeros(self):
        all_zeros = not (
            self._x != 0.0
            or self._y != 0.0
            or self._z != 0.0
            or self._rx != 0.0
            or self._ry != 0.0
            or self._rz != 0.0
        )
        if all_zeros is not self._all_zeros:
            self._all_zeros_published = False
            self._all_zeros = all_zeros
            self.activeChanged.emit(self.active)

    @Property(int, notify=autorepeatIntervalChanged)
    def autorepeatInterval(self):
        return self._autorepeat_interval

    @autorepeatInterval.setter
    def autorepeatInterval(self, value):
        if value == self._autorepeat_interval:
            return
        self._autorepeat_interval = value
        self.autorepeatIntervalChanged.emit(value)

    @Property(bool, notify=enabledChanged)
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if value == self._enabled:
            return
        self._enabled = value
        self.enabledChanged.emit(value)
        self.activeChanged.emit(self.active)

    @Slot()
    def _shutdown(self):
        self._pub.unregister()

import rospy
from PySide6.QtQml import QQmlPropertyMap, QPyQmlParserStatus, QmlElement
from PySide6.QtCore import Property, Signal, Slot, QTimer

from control_msgs.msg import JointJog

from robot_common.joint_urdf import read_robot_description

from ...qt_helpers import ensure_cleanup

DEFAULT_AUTOREPEAT_INTERVAL = 250
JOG_COMMAND_TOPIC = 'jog_arm_server/joint_delta_jog_cmds'

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class JointJogControl(QPyQmlParserStatus):
    """
    Interface for jogging robot joints via the jog_arm server.
    """

    autorepeatIntervalChanged = Signal(int)
    enabledChanged = Signal(bool)
    activeChanged = Signal(bool)
    baseLinkChanged = Signal(str)
    jointNamePrefixChanged = Signal(str)

    def __init__(
        self,
        parent=None,
        enabled=False,
        autorepeat_interval=DEFAULT_AUTOREPEAT_INTERVAL,
        base_link='',
        joint_name_prefix='',
    ):
        super().__init__(parent)

        self._joint_order = []
        self._joint_map = {}
        self._joints = QQmlPropertyMap()
        self._autorepeat_interval = autorepeat_interval
        self._timer = QTimer(self)
        self._enabled = enabled
        self._all_zeros = True
        self._all_zeros_published = False
        self._base_link = base_link
        self._joint_name_prefix = joint_name_prefix

        self._pub = None
        self._component_completed = False

        ensure_cleanup(self._shutdown)

        if enabled:
            self._start()

    def classBegin(self):
        pass

    def componentComplete(self):
        if self._pub is None:
            self._start()

    @Property(QQmlPropertyMap, constant=True)
    def joints(self):
        return self._joints

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._enabled and not self._all_zeros

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

    @Property(str, notify=baseLinkChanged)
    def baseLink(self):
        return self._base_link

    @baseLink.setter
    def baseLink(self, value):
        if value == self._base_link:
            return
        self._base_link = value
        self.baseLinkChanged.emit(value)

    @Property(str, notify=jointNamePrefixChanged)
    def jointNamePrefix(self):
        return self._joint_name_prefix

    @jointNamePrefix.setter
    def jointNamePrefix(self, value):
        if value == self._joint_name_prefix:
            return
        self._joint_name_prefix = value
        self.jointNamePrefixChanged.emit(value)

    def _start(self):
        self._pub = rospy.Publisher(JOG_COMMAND_TOPIC, JointJog, queue_size=1)

        self._timer.timeout.connect(self._publish_status)
        self._joints.valueChanged.connect(self._on_value_changed)
        self.autorepeatIntervalChanged.connect(self._update_timer)
        self.enabledChanged.connect(self._update_timer)
        self.baseLinkChanged.connect(self._read_robot_description)

        self._read_robot_description()
        self._update_timer()

    @Slot()
    def _shutdown(self):
        self._pub.unregister()

    @Slot()
    def _read_robot_description(self):
        joint_order = []
        for key in self._joints.keys():
            self._joints.clear(key)
        for i, node in enumerate(read_robot_description(self._base_link)):
            name = node.data.getAttribute('name')

            if self._joint_name_prefix and not name.startswith(
                self._joint_name_prefix
            ):
                continue

            joint_order.append(name)
            id_ = str(i + 1)
            self._joint_map[name] = id_
            self._joint_map[id_] = name
            self._joints.insert(name, 0.0)
            self._joints.insert(id_, 0.0)
        self._joint_order = joint_order

    def _update_timer(self):
        if self._timer.isActive():
            self._timer.stop()
        if not self._enabled:
            return
        if self._autorepeat_interval > 0:
            self._timer.setInterval(self._autorepeat_interval)
            self._timer.start()
        self._publish_status()

    @Slot()
    def _publish_status(self):
        if self._all_zeros and self._all_zeros_published:
            return
        jj = JointJog()
        jj.header.stamp = rospy.Time.now()
        for name in self._joint_order:
            jj.joint_names.append(name)
            value = float(self._joints.value(name))
            jj.velocities.append(value)
        self._pub.publish(jj)
        self._all_zeros_published = True

    def _update_all_zeros(self):
        all_zeros = all(
            self._joints.value(key) == 0.0 for key in self._joints.keys()
        )
        if self._all_zeros is not all_zeros:
            self._all_zeros_published = False
            self._all_zeros = all_zeros
            self.activeChanged.emit(self.active)

    @Slot(str, 'QVariant')
    def _on_value_changed(self, key, value):
        if key not in self._joint_map:
            return

        other = self._joint_map[key]
        self._joints.insert(other, value)

        self._update_all_zeros()
        self._update_timer()

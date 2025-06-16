from PySide6.QtCore import (
    Slot,
    Signal,
    Property,
    QObject,
    QThread,
)
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

import rospy
from rviz.msg import ObjectProperty
from rviz.srv import SetProperties, SetPropertiesRequest

from ...qt_helpers import MultiSlot, ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.preview'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class RvizObjectWorker(QObject):
    SERVICE_TIMEOUT_S = 5.0

    requestComplete = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._set_property_srv = None
        self.service_address = ''

    @Slot()
    def init(self):
        self._set_property_srv = rospy.ServiceProxy(
            self.service_address, SetProperties
        )

    @Slot(str, list)
    def setProperties(self, name, properties):
        try:
            self._set_property_srv.wait_for_service(
                timeout=self.SERVICE_TIMEOUT_S
            )
        except rospy.ROSException as e:
            self.requestComplete.emit(False, str(e))
            return
        try:
            req = SetPropertiesRequest()
            req.object_name = name
            req.properties = properties
            result = self._set_property_srv(req)
        except rospy.ServiceException as e:
            self.requestComplete.emit(False, str(e))
        else:
            self.requestComplete.emit(result.success, "")


class RvizObject(QObject):
    SET_PROPERTIES_SERVICE = ''

    nameChanged = Signal(str)
    _set_properties = Signal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._name = ""
        self._properties = []

        self._worker = RvizObjectWorker()
        self._worker.service_address = self.SET_PROPERTIES_SERVICE
        self._worker_thread = QThread()
        self._worker_thread.started.connect(self._worker.init)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.start()
        self._set_properties.connect(self._worker.setProperties)
        self._worker.requestComplete.connect(self._on_request_complete)
        ensure_cleanup(self._on_destroyed)

    @MultiSlot(str, [str, bool, float, QColor])
    def setPropertyValue(self, key, value):
        prop = ObjectProperty()
        prop.key = key
        if isinstance(value, bool):
            prop.value_type = ObjectProperty.BOOL_VALUE
            prop.bool_value = value
        elif isinstance(value, float):
            prop.value_type = ObjectProperty.FLOAT_VALUE
            prop.float_value = value
        elif isinstance(value, str):
            prop.value_type = ObjectProperty.STRING_VALUE
            prop.string_value = value
        elif isinstance(value, QColor):
            prop.value_type = ObjectProperty.STRING_VALUE
            prop.string_value = value.name()
        else:
            rospy.logwarn(self.tr(f"Unsupported value type: {type(value)}"))
            return False
        self._properties.append(prop)

    @Slot()
    def apply(self):
        self._set_properties.emit(self._name, self._properties)
        self._properties = []

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name == self._name:
            return
        self._name = name
        self.nameChanged.emit(name)

    @Slot(bool, str)
    def _on_request_complete(self, success, message):
        if not success:
            rospy.logwarn(self.tr(f"Failed to set rviz properties: {message}"))

    @Slot()
    def _on_destroyed(self):
        if self._worker_thread.isRunning():
            self._worker_thread.quit()


@QmlElement
class RvizDisplay(RvizObject):
    SET_PROPERTIES_SERVICE = '/rviz/set_display_properties'


@QmlElement
class RvizOptions(RvizObject):
    SET_PROPERTIES_SERVICE = '/rviz/set_global_options'


@QmlElement
class RvizView(RvizObject):
    SET_PROPERTIES_SERVICE = '/rviz/set_view_properties'

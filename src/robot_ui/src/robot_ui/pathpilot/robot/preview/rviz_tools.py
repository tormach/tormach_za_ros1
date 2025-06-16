from PySide6.QtCore import Slot, Property, Signal, QObject, QThread
from PySide6.QtQml import QmlElement

import rospy
from rviz.srv import SetCurrentTool, SetCurrentToolRequest
from std_srvs.srv import SetBool, SetBoolRequest

from ...qt_helpers import ensure_cleanup


class RvizToolsWorker(QObject):
    SET_CURRENT_TOOL_SERVICE = '/rviz/set_current_tool'
    SET_INPUT_ENABLED_SERVICE = '/rviz/set_input_enabled'
    SERVICE_TIMEOUT_S = 5.0

    requestComplete = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._set_current_tool_srv = None

    @Slot()
    def init(self):
        self._set_current_tool_srv = rospy.ServiceProxy(
            self.SET_CURRENT_TOOL_SERVICE, SetCurrentTool
        )
        self._set_input_enabled_srv = rospy.ServiceProxy(
            self.SET_INPUT_ENABLED_SERVICE, SetBool
        )

    @Slot(str)
    def setCurrentTool(self, tool_name):
        try:
            self._set_current_tool_srv.wait_for_service(
                timeout=self.SERVICE_TIMEOUT_S
            )
        except rospy.ROSException as e:
            self.requestComplete.emit(False, str(e))
            return
        try:
            req = SetCurrentToolRequest()
            req.tool_name = tool_name
            result = self._set_current_tool_srv(req)
        except rospy.ServiceException as e:
            self.requestComplete.emit(False, str(e))
        else:
            self.requestComplete.emit(result.success, "")

    @Slot(bool)
    def setInputEnabled(self, enabled):
        try:
            self._set_input_enabled_srv.wait_for_service(
                timeout=self.SERVICE_TIMEOUT_S
            )
        except rospy.ROSException as e:
            self.requestComplete.emit(False, str(e))
            return
        try:
            req = SetBoolRequest()
            req.data = enabled
            result = self._set_input_enabled_srv(req)
        except rospy.ServiceException as e:
            self.requestComplete.emit(False, str(e))
        else:
            self.requestComplete.emit(result.success, "")


QML_IMPORT_NAME = 'pathpilot.robot.preview'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class RvizTools(QObject):
    currentToolChanged = Signal(str)
    inputEnabledChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_tool = ""
        self._input_enabled = True

        self._worker = RvizToolsWorker()
        self._worker_thread = QThread()
        self._worker_thread.started.connect(self._worker.init)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.start()
        self.currentToolChanged.connect(self._worker.setCurrentTool)
        self.inputEnabledChanged.connect(self._worker.setInputEnabled)
        self._worker.requestComplete.connect(self._on_request_complete)
        ensure_cleanup(self._on_destroyed)

    @Property(str, notify=currentToolChanged)
    def currentTool(self):
        return self._current_tool

    @currentTool.setter
    def currentTool(self, tool_name):
        if tool_name == self._current_tool:
            return

        self._current_tool = tool_name
        self.currentToolChanged.emit(tool_name)

    @Property(bool, notify=inputEnabledChanged)
    def inputEnabled(self):
        return self._input_enabled

    @inputEnabled.setter
    def input_enabled(self, enabled):
        if enabled == self._input_enabled:
            return

        self._input_enabled = enabled
        self.inputEnabledChanged.emit(enabled)

    @Slot(bool, str)
    def _on_request_complete(self, success, message):
        if not success:
            rospy.logwarn(self.tr(f"Failed to set current tool: {message}"))

    @Slot()
    def _on_destroyed(self):
        if self._worker_thread.isRunning():
            self._worker_thread.quit()

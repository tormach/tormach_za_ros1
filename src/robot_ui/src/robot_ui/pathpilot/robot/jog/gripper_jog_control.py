from PySide6.QtCore import Property, Signal, Slot, QObject
from PySide6.QtQml import QmlElement

from robot_command.execution_commands import GripperInterfaceSingleton

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GripperJogControl(QObject):
    currentPositionChanged = Signal(float)
    commandActiveChanged = Signal(bool)
    successChanged = Signal(bool)
    configuredChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._gripper_interface = GripperInterfaceSingleton()
        self._gripper_interface.on_current_position_changed_cb = (
            self._on_current_position_changed
        )
        self._gripper_interface.on_command_active_changed_cb = (
            self._on_command_active_changed
        )
        self._gripper_interface.on_success_changed_cb = self._on_success_changed
        self._gripper_interface.on_configured_changed_cb = (
            self._on_configured_changed
        )

    @Slot()
    def calibrate(self):
        self._gripper_interface.calibrate()

    @Slot(float, result=bool)
    @Slot(float, float, result=bool)
    @Slot(float, float, bool, result=bool)
    def gotoPosition(self, position, effort=20.0, wait=False):
        return self._gripper_interface.goto_position(position, effort, wait)

    @Property(float, notify=currentPositionChanged)
    def currentPosition(self):
        return self._gripper_interface.current_position

    @Property(bool, notify=commandActiveChanged)
    def commandActive(self):
        return self._gripper_interface.command_active

    @Property(bool, notify=successChanged)
    def success(self):
        return self._gripper_interface.success

    @Property(bool, notify=configuredChanged)
    def configured(self):
        return self._gripper_interface.configured

    def _on_current_position_changed(self, position):
        self.currentPositionChanged.emit(position)

    def _on_command_active_changed(self, active):
        self.commandActiveChanged.emit(active)

    def _on_success_changed(self, success):
        self.successChanged.emit(success)

    def _on_configured_changed(self, configured):
        self.configuredChanged.emit(configured)

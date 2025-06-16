from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtQml import QPyQmlParserStatus, QmlElement

from movej_ik_server.movej_ik_server_handler import MovejIkServerHandler
from movej_ik_server.arm_configs import ArmConfigType
from movej_ik_server_msgs.msg import IKSolverWarning


QML_IMPORT_NAME = 'pathpilot.robot.validator'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class PoseWaypointValidator(QPyQmlParserStatus):
    validChanged = Signal()
    armConfigChanged = Signal()
    revCountChanged = Signal()

    def __init__(self):
        super().__init__()
        self._valid = True
        self._movej_ik_server_handler = MovejIkServerHandler()

    def classBegin(self):
        # This method will be called when QML starts creating an object of this class
        pass

    def componentComplete(self):
        # This method will be called when QML finishes creating an object of this class
        pass

    @Property(bool, notify=validChanged)
    def valid(self):
        return self._valid

    @Property(str, notify=armConfigChanged)
    def armConfig(self):
        return self._arm_config

    @Property(int, notify=revCountChanged)
    def revCount(self):
        return self._rev_count

    @Slot()
    def updateValid(self):
        (
            response,
            success,
        ) = self._movej_ik_server_handler.get_arm_config_service_call()
        print(
            f"Inside updateValid [PYTHON]: valid? {response.is_arm_config_valid} arm_config: {response.arm_config}, rev_count: {response.rev_count}"
        )

        if (
            IKSolverWarning.REQUESTED_CONFIG_NEAR_SINGULARITY
            in response.warning_codes
        ):
            self._valid = False
        else:
            self._valid = True

        # self._valid = response.is_arm_config_valid
        self._arm_config = str(ArmConfigType(response.arm_config))
        self._rev_count = response.rev_count
        self.validChanged.emit()
        self.armConfigChanged.emit()
        self.revCountChanged.emit()

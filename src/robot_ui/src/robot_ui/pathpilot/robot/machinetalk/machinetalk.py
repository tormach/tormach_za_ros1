import rospy
from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QmlElement, QmlSingleton
from robot_command.interfaces.machinetalk_interface import (
    MachinetalkInterfaceSingleton,
    MachinetalkInstanceNotFoundError,
    MachinetalkInstanceNotConnectedError,
)
from machinetalk.protobuf.status_pb2 import (
    LINEAR_UNITS_INCH,
    LINEAR_UNITS_MM,
    LINEAR_UNITS_CM,
    ANGULAR_UNITS_DEGREES,
    ANGULAR_UNITS_GRAD,
    ANGULAR_UNITS_RADIAN,
    TIME_UNITS_MINUTE,
    TIME_UNITS_SECOND,
)

from ..units import Units


QML_IMPORT_NAME = 'pathpilot.robot.machinetalk'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class Machinetalk(QObject):
    LINEAR_UNITS = {
        LINEAR_UNITS_MM: 'mm',
        LINEAR_UNITS_CM: 'cm',
        LINEAR_UNITS_INCH: 'in',
    }
    ANGULAR_UNITS = {
        ANGULAR_UNITS_RADIAN: 'rad',
        ANGULAR_UNITS_DEGREES: 'deg',
        ANGULAR_UNITS_GRAD: 'grad',
    }
    TIME_UNITS = {
        TIME_UNITS_SECOND: 's',
        TIME_UNITS_MINUTE: 'min',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._machinetalk = MachinetalkInterfaceSingleton()

    @Slot(result=list)
    @Slot(str, result=list)
    def getMachinePosition(self, instance=None):
        try:
            status = self._machinetalk.get_status(instance)
        except (
            MachinetalkInstanceNotFoundError,
            MachinetalkInstanceNotConnectedError,
        ) as e:
            rospy.logerr(str(e))
            return []

        if not (status.config and status.motion):
            rospy.logerr("No status or config available")
            return []

        position = status.motion.actual_position
        linear_units, angular_units, _ = self._get_units(status.config)
        pos = Units.to_ros(
            [
                position.x,
                position.y,
                position.z,
            ],
            linear_units,
        ) + Units.to_ros(
            [
                position.a,
                position.b,
                position.c,
            ],
            angular_units,
        )
        return pos

    @Slot(str, result=bool)
    @Slot(str, str, result=bool)
    def executeMdi(self, command, instance=None):
        try:
            self._machinetalk.execute_mdi(command, instance)
            return True
        except (
            MachinetalkInstanceNotFoundError,
            MachinetalkInstanceNotConnectedError,
        ) as e:
            rospy.logerr(str(e))
            return False

    @Slot(result=list)
    @Slot(str, result=list)
    def getUnits(self, instance=None):
        try:
            status = self._machinetalk.get_status(instance)
        except (
            MachinetalkInstanceNotFoundError,
            MachinetalkInstanceNotConnectedError,
        ) as e:
            rospy.logerr(str(e))
            return []

        if not status.config:
            rospy.logerr("No config available")
            return []

        return list(self._get_units(status.config))

    @staticmethod
    def _get_units(config):
        linear_units = Machinetalk.LINEAR_UNITS[config.linear_units]
        angular_units = Machinetalk.ANGULAR_UNITS[config.angular_units]
        time_units = Machinetalk.TIME_UNITS[config.time_units]
        return linear_units, angular_units, time_units

from enum import IntEnum
from PySide6.QtCore import QObject, QEnum
from PySide6.QtQml import QmlElement, QmlUncreatable
from machinekit import hal

QML_IMPORT_NAME = 'pathpilot.robot.hal'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class PinType(IntEnum):
    Float = hal.HAL_FLOAT
    Bit = hal.HAL_BIT
    S32 = hal.HAL_S32
    U32 = hal.HAL_U32


class PinDirection(IntEnum):
    Out = hal.HAL_OUT
    In = hal.HAL_IN
    IO = hal.HAL_IO


@QmlElement
@QmlUncreatable("Hal is not creatable from QML")
class Hal(QObject):
    QEnum(PinType)
    QEnum(PinDirection)

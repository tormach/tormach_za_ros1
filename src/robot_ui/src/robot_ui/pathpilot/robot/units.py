import pint

from PySide6.QtCore import QObject, Slot, Property
from PySide6.QtQml import QJSValue, QmlElement, QmlSingleton

# defines the application-wide unit registry
ureg = pint.UnitRegistry()
pint.set_application_registry(ureg)

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class Units(QObject):
    """Unit conversion functions."""

    ROS_UNIT_FOR_DIMENSION = {
        frozenset({'[length]': 1}.items()): 'm',
        frozenset(): 'rad',
        frozenset({'[length]': 1, '[time]': -1}.items()): 'm/s',
        frozenset({'[length]': 1, '[time]': -2}.items()): 'm/s^2',
    }
    ROS_LINEAR_UNIT = "m"
    ROS_ANGULAR_UNIT = "rad"

    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(str, constant=True)
    def rosLinearUnit(self):
        return self.ROS_LINEAR_UNIT

    @Property(str, constant=True)
    def rosAngularUnit(self):
        return self.ROS_ANGULAR_UNIT

    @Slot(float, str, result=float)
    @Slot(list, str, result=list)
    def fromRos(self, value, to):
        return Units.from_ros(value, to)

    @staticmethod
    def from_ros(value, to):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        from_ = Units.ROS_UNIT_FOR_DIMENSION[
            frozenset(ureg.Unit(to).dimensionality.items())
        ]
        if isinstance(value, list):
            return [ureg.Quantity(v, from_).to(to).magnitude for v in value]
        else:
            return ureg.Quantity(value, from_).to(to).magnitude

    @Slot(float, str, result=float)
    @Slot(list, str, result=list)
    def toRos(self, value, from_):
        return Units.to_ros(value, from_)

    @staticmethod
    def to_ros(value, from_):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        to = Units.ROS_UNIT_FOR_DIMENSION[
            frozenset(ureg.Unit(from_).dimensionality.items())
        ]
        if isinstance(value, list):
            return [ureg.Quantity(v, from_).to(to).magnitude for v in value]
        else:
            return ureg.Quantity(value, from_).to(to).magnitude

    @Slot(float, str, str, result=float)
    @Slot(list, str, result=list)
    def fromTo(self, value, from_, to):
        return Units.from_to(value, from_, to)

    @staticmethod
    def from_to(value, from_, to):
        value = value.toVariant() if isinstance(value, QJSValue) else value
        if isinstance(value, list):
            return [ureg.Quantity(v, from_).to(to).magnitude for v in value]
        else:
            return ureg.Quantity(value, from_).to(to).magnitude

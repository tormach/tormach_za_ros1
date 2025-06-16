from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QQmlPropertyMap, QPyQmlParserStatus, QmlElement
from PySide6.QtQuick import QQuickItem

from .hal_pin import HalPin


QML_IMPORT_NAME = 'pathpilot.robot.hal'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class HalIoGroup(QQuickItem, QPyQmlParserStatus):
    """
    This class groups together HalPin objects for easier access via a list or map.
    """

    pinsChanged = Signal()
    containerItemChanged = Signal(QObject)

    def __init__(self, parent=None, container_item=None):
        super().__init__(parent)

        self._pins = []
        self._pins_by_name = QQmlPropertyMap()
        self._container_item = (
            container_item if container_item is not None else self
        )

    def classBegin(self):
        pass

    def componentComplete(self):
        self.update()

    @Slot()
    def update(self):
        pins = []
        objects = self._recurse_object(self._container_item.children())
        for pin in objects:
            if (not pin.enabled) or pin.name == '':
                continue
            pins.append(pin)
        self._pins = pins
        self.pinsChanged.emit()
        self._update_pins_by_name()

    def _recurse_object(self, object_list):
        items = []

        for item in object_list:
            if isinstance(item, HalPin):
                items.append(item)

            if any(item.children()):
                items += self._recurse_object(item.children())

        return items

    @Property(list, notify=pinsChanged)
    def pins(self):
        return self._pins

    @Property(QQmlPropertyMap, constant=True)
    def pinsByName(self):
        return self._pins_by_name

    @Property(QObject, notify=containerItemChanged)
    def containerItem(self):
        return self._container_item

    @containerItem.setter
    def containerItem(self, value):
        if value == self._container_item:
            return
        self._container_item = value
        self.containerItemChanged.emit(value)

    def _update_pins_by_name(self):
        added = set()
        for pin in self.pins:
            self._pins_by_name.insert(pin.name, pin)
            added.add(pin.name)

        removed = set(self._pins_by_name.keys()) - added
        for name in removed:
            self._pins_by_name.clear(name)

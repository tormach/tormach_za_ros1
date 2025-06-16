import weakref

from PySide6.QtCore import QObject, Signal, Property
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GlobalObject(QObject):
    __instances = weakref.WeakSet()
    __values = weakref.WeakValueDictionary()

    objectChanged = Signal(QObject)
    nameChanged = Signal(str)

    def __init__(self, parent=None, name="", object_=None):
        super().__init__(parent)
        self.__instances.add(self)

        self._object = weakref.ref(object_) if object_ else None
        self._name = name

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == self._name:
            return
        self._name = value
        self.nameChanged.emit(value)
        if self._object:
            self.object = self._object()

    @Property(QObject, notify=objectChanged)
    def object(self):
        return self.__values.get(self._name, None)

    @object.setter
    def object(self, value):
        self._object = weakref.ref(value) if value else None
        if self._name == '':
            return
        if value == self.__values.get(self._name, None):
            return
        self.__values[self._name] = value
        for instance in (i for i in self.__instances if i.name == self._name):
            instance.objectChanged.emit(value)

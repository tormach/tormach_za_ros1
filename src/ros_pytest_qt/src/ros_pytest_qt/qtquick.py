from PySide6.QtCore import QUrl, QPoint, Qt, QObject, QByteArray
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest


def find_object(engine, name):
    def recurse(item, name_):
        if item.objectName() == name_:
            return item
        for child in item.children():
            found = recurse(child, name_)
            if found:
                return found
        return None

    return recurse(engine.rootObjects()[0], name)


def find_object_class_name(engine, name):
    def recurse(item, name_):
        if item.metaObject().className().split('_')[0] == name_:
            return item
        for child in item.children():
            found = recurse(child, name_)
            if found:
                return found
        return None

    return recurse(engine.rootObjects()[0], name)


def click_item(item, window):
    point = item.mapToScene(QPoint(0, 0))
    point.setX(point.x() + item.width() / 2)
    point.setY(point.y() + item.height() / 2)
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)


class QtQuickPropertyWrapper:
    """
    Simplifies access to properties of QtQuick items.
    """

    def __init__(self, wrapped):
        self.__dict__['_wrapped'] = wrapped

    def __getattr__(self, key):
        if hasattr(self.__dict__['_wrapped'], key):
            return getattr(self.__dict__['_wrapped'], key)
        return self.__dict__['_wrapped'].property(key)

    def __setattr__(self, key, value):
        if hasattr(self.__dict__['_wrapped'], key):
            setattr(self.__dict__['_wrapped'], key, value)
        else:
            self.__dict__['_wrapped'].setProperty(key, value)

    def __delattr__(self, item):
        delattr(self.__dict__['_wrapped'], item)


class QtQuickTestWindow(QObject):
    def __init__(self, path, visible=False, parent=None):
        super().__init__(parent)
        self.engine = None
        self.window = None
        self.loader = None
        self.visible = visible
        self._component = None
        self._url = QUrl.fromLocalFile(path)
        self._create_window()

    def _create_window(self):
        qml = '''\
import QtQuick
import QtQuick.Controls
ApplicationWindow {{
  objectName: "_window"
  visible: {visible}
  width: loader.item ? loader.item.width : 0
  height: loader.item ? loader.item.height : 0
  Loader {{
    readonly property bool errored: status === Loader.Error
    id: loader
    objectName: "_loader"
  }}
}}'''.format(
            visible='true' if self.visible else 'false'
        )
        self.engine = QQmlApplicationEngine()
        self.engine.loadData(QByteArray(qml.encode()), self._url)
        self.loader = find_object(self.engine, '_loader')
        self.window = find_object(self.engine, '_window')

    def load_data(self, data):
        component = QQmlComponent(self.engine)
        component.setData(QByteArray(data.encode()), self._url)
        if component.isError():
            print("QML component errors:")
            for e in component.errors():
                print(e.toString())
        self.loader.setProperty('sourceComponent', component)
        self.loader.setProperty('active', True)
        self._component = component
        assert not self.loader.property(
            'errored'
        ), 'Loading QML component failed'

    def load(self, path):
        self.loader.setProperty('sourceComponent', None)
        self.loader.setProperty('source', QUrl.fromLocalFile(path))
        self.loader.setProperty('active', True)
        assert not self.loader.property(
            'errored'
        ), 'Loading QML component failed'

    def click_item(self, item):
        point = item.mapToScene(QPoint(0, 0))
        point.setX(point.x() + item.width() / 2)
        point.setY(point.y() + item.height() / 2)
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, point)

    def item(self, name=None, class_=None):
        if name:
            return QtQuickPropertyWrapper(find_object(self.engine, name))
        if class_:
            return QtQuickPropertyWrapper(
                find_object_class_name(self.engine, class_)
            )

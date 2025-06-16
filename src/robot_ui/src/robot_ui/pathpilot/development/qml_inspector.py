from PySide6.QtCore import QObject, Slot, QPointF
from PySide6.QtQml import QmlElement, QmlSingleton
from PySide6.QtQuick import QQuickItem

QML_IMPORT_NAME = 'pathpilot.development'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class QmlInspector(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(QQuickItem, int, int, result=QQuickItem)
    def findTopItem(self, item: QQuickItem, x: int, y: int):
        child_item = item
        original_point = QPointF(x, y)
        scene_point = item.mapToScene(original_point)
        while True:
            point = child_item.mapFromScene(scene_point)
            new_item = child_item.childAt(point.x(), point.y())
            if new_item:
                if new_item.objectName() == 'notebook_background':
                    for child in child_item.children():
                        if child.isVisible():
                            new_item = child
                            break
                child_item = new_item
            else:
                break
        return child_item

    @Slot(QQuickItem, result=QQuickItem)
    def findProjectItem(self, item: QQuickItem):
        new_item = item
        while True:
            parent_item = new_item.parentItem()
            if parent_item:
                new_item = parent_item
                if 'QMLTYPE' in new_item.metaObject().className():
                    return new_item
            else:
                break
        return item

    @Slot(QQuickItem, result=str)
    def inspectProjectItems(self, item: QQuickItem):
        new_item = item
        level = 0
        output = []
        while True:
            output.append(new_item.metaObject().className().split('_')[0])
            parent_item = self.findProjectItem(new_item)
            if parent_item == new_item:
                break
            level += 1
            new_item = parent_item
        output_levels = [
            f"{'-'*i}> {item}" for i, item in enumerate(reversed(output))
        ]
        return '\n'.join(output_levels)

    @Slot(QQuickItem, result=str)
    def inspectItem(self, item: QQuickItem):
        meta_object = item.metaObject()
        text = f"Class: {meta_object.className()}\n"
        text += "Properties:\n"
        props = {}
        for i in range(meta_object.propertyCount()):
            prop = meta_object.property(i)
            try:
                props[prop.name()] = str(item.property(prop.name()))
            except RuntimeError:
                continue
        for key in sorted(props.keys()):
            text += f"{key} = {props[key]}\n"
        text += "Methods:\n"
        methods = []
        for i in range(meta_object.methodCount()):
            method = meta_object.method(i)
            methods.append(method)
        for method in sorted(methods, key=lambda x: x.name()):
            text += f"{method.name().data().decode()}()\n"
        return text

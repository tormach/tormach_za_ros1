import types

from PySide6.QtCore import QEvent, QCoreApplication, QObject, QTimer, Slot
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QmlElement, QmlSingleton, qmlEngine

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class GlobalShortcuts(QObject):
    IGNORED_OBJECT_NAMES = ('textField', 'textArea')

    def __init__(self, parent=None):
        super().__init__(parent)

        QCoreApplication.instance().installEventFilter(self)

        # workaround to get QML engine instance
        self._engine = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._connect_to_engine)
        self._timer.start(100)

        self._shortcut_handlers = set()

    @Slot()
    def _connect_to_engine(self):
        engine = qmlEngine(self)
        if engine is None:
            return
        self._engine = engine
        self._engine.installEventFilter(self)
        self._timer.stop()

    def eventFilter(self, obj, event):
        if obj.objectName() in self.IGNORED_OBJECT_NAMES or isinstance(
            obj, QQuickWindow
        ):
            pass

        elif event.type() == QEvent.KeyPress:
            for handler in self._shortcut_handlers:
                if handler.handle_key_press_event(obj, event):
                    return True

        elif event.type() == QEvent.KeyRelease:
            for handler in self._shortcut_handlers:
                if handler.handle_key_release_event(obj, event):
                    return True

        return super().eventFilter(obj, event)

    def register_shortcut_handler(self, instance):
        has_key_press_method = isinstance(
            getattr(instance, "handle_key_press_event"), types.MethodType
        )
        has_key_release_method = isinstance(
            getattr(instance, "handle_key_release_event"), types.MethodType
        )
        if not (has_key_press_method and has_key_release_method):
            raise TypeError(
                "Shortcut handler must implement handle_key_press_event and handle_key_release_event"
            )
        self._shortcut_handlers.add(instance)

    def unregister_shortcut_handler(self, instance):
        self._shortcut_handlers.remove(instance)

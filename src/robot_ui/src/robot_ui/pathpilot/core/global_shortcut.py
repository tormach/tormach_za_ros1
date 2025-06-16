from PySide6.QtCore import QObject, Property, Signal, Slot, Qt
from PySide6.QtQml import QmlElement

from .global_shortcuts import GlobalShortcuts
from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GlobalShortcut(QObject):
    globalShortcutsChanged = Signal()
    enabledChanged = Signal(bool)
    keyChanged = Signal(int)
    modifiersChanged = Signal(Qt.KeyboardModifiers)
    keyPressedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._global_shortcuts = QObject()
        self._enabled = True
        self._key = 0
        self._modifiers = 0
        self._key_pressed = False

        ensure_cleanup(self._cleanup)

    @Property(GlobalShortcuts, notify=globalShortcutsChanged)
    def globalShortcuts(self):
        return self._global_shortcuts

    @globalShortcuts.setter
    def globalShortcuts(self, value):
        if value == self._global_shortcuts:
            return

        if hasattr(self._global_shortcuts, 'unregister_shortcut_handler'):
            self._global_shortcuts.unregister_shortcut_handler(self)
        if value is not None:
            value.register_shortcut_handler(self)
        self._global_shortcuts = value
        self.globalShortcutsChanged.emit()

    @Property(bool, notify=enabledChanged)
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if value == self._enabled:
            return
        self._enabled = value
        self.enabledChanged.emit(value)

        if not value:
            self._stop()

    @Property(int, notify=keyChanged)
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        if value == self._key:
            return
        self._key = value
        self.keyChanged.emit(value)

    @Property(Qt.KeyboardModifiers, notify=modifiersChanged)
    def modifiers(self):
        return self._modifiers

    @modifiers.setter
    def modifiers(self, value):
        if value == self._modifiers:
            return
        self._modifiers = value
        self.modifiersChanged.emit(value)

    @Property(bool, notify=keyPressedChanged)
    def keyPressed(self):
        return self._key_pressed

    @keyPressed.setter
    def keyPressed(self, value):
        if value == self._key_pressed:
            return
        self._key_pressed = value
        self.keyPressedChanged.emit(value)

    def handle_key_press_event(self, _obj, event):
        if not self._enabled:
            return False

        if event.isAutoRepeat():
            return True

        if self._modifiers and not (event.modifiers & self._modifiers):
            return False

        if event.key() == self._key:
            self._key_pressed = True
            self.keyPressedChanged.emit(self._key_pressed)
            return True

        return False

    def handle_key_release_event(self, _obj, event):
        if not self._enabled:
            return False

        if event.isAutoRepeat():
            return True

        if (
            self._modifiers
            and not (event.modifiers & self._modifiers)
            and self._key_pressed
        ):
            self._key_pressed = False
            self.keyPressedChanged.emit(self._key_pressed)

        if event.key() == self._key and self._key_pressed:
            self._key_pressed = False
            self.keyPressedChanged.emit(self._key_pressed)
            return True

        return False

    def _stop(self):
        if self._key_pressed:
            self._key_pressed = False
            self.keyPressedChanged.emit(self._key_pressed)

    @Slot()
    def _cleanup(self):
        if self._global_shortcuts is not None:
            self._global_shortcuts.unregister_shortcut_handler(self)
        self._global_shortcuts = None

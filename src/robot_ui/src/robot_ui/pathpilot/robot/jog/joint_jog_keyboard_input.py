from PySide6.QtCore import (
    Property,
    Signal,
    QObject,
    Slot,
    Qt,
)
from PySide6.QtQml import QmlElement

from ...core import GlobalShortcuts
from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class JointJogKeyboardInput(QObject):
    SELECT_JOINT1_KEY = Qt.Key_1
    SELECT_JOINT2_KEY = Qt.Key_2
    SELECT_JOINT3_KEY = Qt.Key_3
    SELECT_JOINT4_KEY = Qt.Key_4
    SELECT_JOINT5_KEY = Qt.Key_5
    SELECT_JOINT6_KEY = Qt.Key_6
    INCREMENT_KEY = Qt.Key_0
    DECREMENT_KEY = Qt.Key_9
    RAPID_MODIFIER = Qt.ShiftModifier

    globalShortcutsChanged = Signal(GlobalShortcuts)
    enabledChanged = Signal(bool)
    incrementPressedChanged = Signal(bool)
    decrementPressedChanged = Signal(bool)
    rapidActiveChanged = Signal(bool)
    jointSelected = Signal(int, arguments=['index'])

    def __init__(self, parent=None):
        super().__init__(parent)

        self._enabled = False
        self._global_shortcuts = None

        self._increment_pressed = False
        self._decrement_pressed = False
        self._rapid_active = False

        ensure_cleanup(self._cleanup)

    @Property(GlobalShortcuts, notify=globalShortcutsChanged)
    def globalShortcuts(self):
        return self._global_shortcuts

    @globalShortcuts.setter
    def globalShortcuts(self, value):
        if value == self._global_shortcuts:
            return

        if self._global_shortcuts is not None:
            self._global_shortcuts.unregister_shortcut_handler(self)
        if value is not None:
            value.register_shortcut_handler(self)
        self._global_shortcuts = value
        self.globalShortcutsChanged.emit(value)

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

    @Property(bool, notify=incrementPressedChanged)
    def incrementPressed(self):
        return self._increment_pressed

    @Property(bool, notify=decrementPressedChanged)
    def decrementPressed(self):
        return self._decrement_pressed

    @Property(bool, notify=rapidActiveChanged)
    def rapidActive(self):
        return self._rapid_active

    def handle_key_press_event(self, _obj, event):
        if not self._enabled:
            return False

        if event.isAutoRepeat():
            return True

        if event.modifiers() & Qt.ShiftModifier and not self._rapid_active:
            self._rapid_active = True
            self.rapidActiveChanged.emit(self._rapid_active)

        if event.key() == self.INCREMENT_KEY:
            self._increment_pressed = True
            self.incrementPressedChanged.emit(self._increment_pressed)
            return True
        elif event.key() == self.DECREMENT_KEY:
            self._decrement_pressed = True
            self.decrementPressedChanged.emit(self._decrement_pressed)
            return True
        elif event.key() == self.SELECT_JOINT1_KEY:
            self.jointSelected.emit(1)
            return True
        elif event.key() == self.SELECT_JOINT2_KEY:
            self.jointSelected.emit(2)
            return True
        elif event.key() == self.SELECT_JOINT3_KEY:
            self.jointSelected.emit(3)
            return True
        elif event.key() == self.SELECT_JOINT4_KEY:
            self.jointSelected.emit(4)
            return True
        elif event.key() == self.SELECT_JOINT5_KEY:
            self.jointSelected.emit(5)
            return True
        elif event.key() == self.SELECT_JOINT6_KEY:
            self.jointSelected.emit(6)
            return True

        return False

    def handle_key_release_event(self, _obj, event):
        if not self._enabled:
            return False

        if event.isAutoRepeat():
            return True

        if not (event.modifiers() & Qt.ShiftModifier) and self._rapid_active:
            self._rapid_active = False
            self.rapidActiveChanged.emit(self._rapid_active)

        if event.key() == self.INCREMENT_KEY and self._increment_pressed:
            self._increment_pressed = False
            self.incrementPressedChanged.emit(self._increment_pressed)
            return True
        elif event.key() == self.DECREMENT_KEY and self._decrement_pressed:
            self._decrement_pressed = False
            self.decrementPressedChanged.emit(self._decrement_pressed)
            return True

        return False

    def _stop(self):
        if self._increment_pressed:
            self._increment_pressed = False
            self.incrementPressedChanged.emit(self._increment_pressed)
        if self._decrement_pressed:
            self._decrement_pressed = False
            self.decrementPressedChanged.emit(self._decrement_pressed)
        if self._rapid_active:
            self._rapid_active = False
            self.rapidActiveChanged.emit(self._rapid_active)

    @Slot()
    def _cleanup(self):
        if self._global_shortcuts is not None:
            self._global_shortcuts.unregister_shortcut_handler(self)
        self._global_shortcuts = None

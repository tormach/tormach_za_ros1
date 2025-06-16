from PySide6.QtCore import (
    Property,
    Signal,
    QObject,
    Qt,
    Slot,
)
from PySide6.QtQml import QmlElement

from ...core import GlobalShortcuts
from ...qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CartesianJogKeyboardInput(QObject):
    X_MINUS_KEY = Qt.Key_Left
    X_PLUS_KEY = Qt.Key_Right
    Y_MINUS_KEY = Qt.Key_Down
    Y_PLUS_KEY = Qt.Key_Up
    Z_MINUS_KEY = Qt.Key_PageDown
    Z_PLUS_KEY = Qt.Key_PageUp
    A_MINUS_KEY = Qt.Key_Comma
    A_PLUS_KEY = Qt.Key_Period
    B_MINUS_KEY = Qt.Key_Semicolon
    B_PLUS_KEY = Qt.Key_Apostrophe
    C_MINUS_KEY = Qt.Key_BracketLeft
    C_PLUS_KEY = Qt.Key_BracketRight
    RAPID_MODIFIER = Qt.ShiftModifier
    TOGGLE_CONTINUOUS_KEY = Qt.Key_C
    TOGGLE_FRAME_KEY = Qt.Key_F
    TOGGLE_STEP_SIZE_KEY = Qt.Key_S

    globalShortcutsChanged = Signal(GlobalShortcuts)
    enabledChanged = Signal(bool)
    xMinusPressedChanged = Signal(bool)
    xPlusPressedChanged = Signal(bool)
    yMinusPressedChanged = Signal(bool)
    yPlusPressedChanged = Signal(bool)
    zMinusPressedChanged = Signal(bool)
    zPlusPressedChanged = Signal(bool)
    aMinusPressedChanged = Signal(bool)
    aPlusPressedChanged = Signal(bool)
    bMinusPressedChanged = Signal(bool)
    bPlusPressedChanged = Signal(bool)
    cMinusPressedChanged = Signal(bool)
    cPlusPressedChanged = Signal(bool)
    rapidActiveChanged = Signal(bool)
    toggleContinuousTriggered = Signal()
    toggleFrameTriggered = Signal()
    toggleStepSizeTriggered = Signal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self._enabled = False
        self._global_shortcuts = None

        self._x_minus_pressed = False
        self._x_plus_pressed = False
        self._y_minus_pressed = False
        self._y_plus_pressed = False
        self._z_minus_pressed = False
        self._z_plus_pressed = False
        self._a_minus_pressed = False
        self._a_plus_pressed = False
        self._b_minus_pressed = False
        self._b_plus_pressed = False
        self._c_minus_pressed = False
        self._c_plus_pressed = False
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

    @Property(bool, notify=xMinusPressedChanged)
    def xMinusPressed(self):
        return self._x_minus_pressed

    @Property(bool, notify=xPlusPressedChanged)
    def xPlusPressed(self):
        return self._x_plus_pressed

    @Property(bool, notify=yMinusPressedChanged)
    def yMinusPressed(self):
        return self._y_minus_pressed

    @Property(bool, notify=yPlusPressedChanged)
    def yPlusPressed(self):
        return self._y_plus_pressed

    @Property(bool, notify=zMinusPressedChanged)
    def zMinusPressed(self):
        return self._z_minus_pressed

    @Property(bool, notify=zPlusPressedChanged)
    def zPlusPressed(self):
        return self._z_plus_pressed

    @Property(bool, notify=aMinusPressedChanged)
    def aMinusPressed(self):
        return self._a_minus_pressed

    @Property(bool, notify=aPlusPressedChanged)
    def aPlusPressed(self):
        return self._a_plus_pressed

    @Property(bool, notify=bMinusPressedChanged)
    def bMinusPressed(self):
        return self._b_minus_pressed

    @Property(bool, notify=bPlusPressedChanged)
    def bPlusPressed(self):
        return self._b_plus_pressed

    @Property(bool, notify=cMinusPressedChanged)
    def cMinusPressed(self):
        return self._c_minus_pressed

    @Property(bool, notify=cPlusPressedChanged)
    def cPlusPressed(self):
        return self._c_plus_pressed

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

        if event.key() == self.X_MINUS_KEY:
            self._x_minus_pressed = True
            self.xMinusPressedChanged.emit(self._x_minus_pressed)
            return True
        elif event.key() == self.X_PLUS_KEY:
            self._x_plus_pressed = True
            self.xPlusPressedChanged.emit(self._x_plus_pressed)
            return True
        elif event.key() == self.Y_MINUS_KEY:
            self._y_minus_pressed = True
            self.yMinusPressedChanged.emit(self._y_minus_pressed)
            return True
        elif event.key() == self.Y_PLUS_KEY:
            self._y_plus_pressed = True
            self.yPlusPressedChanged.emit(self._y_plus_pressed)
            return True
        elif event.key() == self.Z_MINUS_KEY:
            self._z_minus_pressed = True
            self.zMinusPressedChanged.emit(self._z_minus_pressed)
            return True
        elif event.key() == self.Z_PLUS_KEY:
            self._z_plus_pressed = True
            self.zPlusPressedChanged.emit(self._z_plus_pressed)
            return True
        elif event.key() == self.A_MINUS_KEY:
            self._a_minus_pressed = True
            self.aMinusPressedChanged.emit(self._a_minus_pressed)
            return True
        elif event.key() == self.A_PLUS_KEY:
            self._a_plus_pressed = True
            self.aPlusPressedChanged.emit(self._a_plus_pressed)
            return True
        elif event.key() == self.B_MINUS_KEY:
            self._b_minus_pressed = True
            self.bMinusPressedChanged.emit(self._b_minus_pressed)
            return True
        elif event.key() == self.B_PLUS_KEY:
            self._b_plus_pressed = True
            self.bPlusPressedChanged.emit(self._b_plus_pressed)
            return True
        elif event.key() == self.C_MINUS_KEY:
            self._c_minus_pressed = True
            self.cMinusPressedChanged.emit(self._c_minus_pressed)
            return True
        elif event.key() == self.C_PLUS_KEY:
            self._c_plus_pressed = True
            self.cPlusPressedChanged.emit(self._c_plus_pressed)
            return True
        elif event.key() == self.TOGGLE_CONTINUOUS_KEY:
            self.toggleContinuousTriggered.emit()
            return True
        elif event.key() == self.TOGGLE_FRAME_KEY:
            self.toggleFrameTriggered.emit()
            return True
        elif event.key() == self.TOGGLE_STEP_SIZE_KEY:
            self.toggleStepSizeTriggered.emit()
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

        if event.key() == self.X_MINUS_KEY and self._x_minus_pressed:
            self._x_minus_pressed = False
            self.xMinusPressedChanged.emit(self._x_minus_pressed)
            return True
        elif event.key() == self.X_PLUS_KEY and self._x_plus_pressed:
            self._x_plus_pressed = False
            self.xPlusPressedChanged.emit(self._x_plus_pressed)
            return True
        elif event.key() == self.Y_MINUS_KEY and self._y_minus_pressed:
            self._y_minus_pressed = False
            self.yMinusPressedChanged.emit(self._y_minus_pressed)
            return True
        elif event.key() == self.Y_PLUS_KEY and self._y_plus_pressed:
            self._y_plus_pressed = False
            self.yPlusPressedChanged.emit(self._y_plus_pressed)
            return True
        elif event.key() == self.Z_MINUS_KEY and self._z_minus_pressed:
            self._z_minus_pressed = False
            self.zMinusPressedChanged.emit(self._z_minus_pressed)
            return True
        elif event.key() == self.Z_PLUS_KEY and self._z_plus_pressed:
            self._z_plus_pressed = False
            self.zPlusPressedChanged.emit(self._z_plus_pressed)
            return True
        elif event.key() == self.A_MINUS_KEY and self._a_minus_pressed:
            self._a_minus_pressed = False
            self.aMinusPressedChanged.emit(self._a_minus_pressed)
            return True
        elif event.key() == self.A_PLUS_KEY and self._a_plus_pressed:
            self._a_plus_pressed = False
            self.aPlusPressedChanged.emit(self._a_plus_pressed)
            return True
        elif event.key() == self.B_MINUS_KEY and self._b_minus_pressed:
            self._b_minus_pressed = False
            self.bMinusPressedChanged.emit(self._b_minus_pressed)
            return True
        elif event.key() == self.B_PLUS_KEY and self._b_plus_pressed:
            self._b_plus_pressed = False
            self.bPlusPressedChanged.emit(self._b_plus_pressed)
            return True
        elif event.key() == self.C_MINUS_KEY and self._c_minus_pressed:
            self._c_minus_pressed = False
            self.cMinusPressedChanged.emit(self._c_minus_pressed)
            return True
        elif event.key() == self.C_PLUS_KEY and self._c_plus_pressed:
            self._c_plus_pressed = False
            self.cPlusPressedChanged.emit(self._c_plus_pressed)
            return True

        return False

    def _stop(self):
        if self._x_minus_pressed:
            self._x_minus_pressed = False
            self.xMinusPressedChanged.emit(self._x_minus_pressed)
        if self._x_plus_pressed:
            self._x_plus_pressed = False
            self.xPlusPressedChanged.emit(self._x_plus_pressed)
        if self._y_minus_pressed:
            self._y_minus_pressed = False
            self.yMinusPressedChanged.emit(self._y_minus_pressed)
        if self._y_plus_pressed:
            self._y_plus_pressed = False
            self.yPlusPressedChanged.emit(self._y_plus_pressed)
        if self._z_minus_pressed:
            self._z_minus_pressed = False
            self.zMinusPressedChanged.emit(self._z_minus_pressed)
        if self._z_plus_pressed:
            self._z_plus_pressed = False
            self.zPlusPressedChanged.emit(self._z_plus_pressed)
        if self._a_minus_pressed:
            self._a_minus_pressed = False
            self.aMinusPressedChanged.emit(self._a_minus_pressed)
        if self._a_plus_pressed:
            self._a_plus_pressed = False
            self.aPlusPressedChanged.emit(self._a_plus_pressed)
        if self._b_minus_pressed:
            self._b_minus_pressed = False
            self.bMinusPressedChanged.emit(self._b_minus_pressed)
        if self._b_plus_pressed:
            self._b_plus_pressed = False
            self.bPlusPressedChanged.emit(self._b_plus_pressed)
        if self._c_minus_pressed:
            self._c_minus_pressed = False
            self.cMinusPressedChanged.emit(self._c_minus_pressed)
        if self._c_plus_pressed:
            self._c_plus_pressed = False
            self.cPlusPressedChanged.emit(self._c_plus_pressed)
        if self._rapid_active:
            self._rapid_active = False
            self.rapidActiveChanged.emit(self._rapid_active)

    @Slot()
    def _cleanup(self):
        if self._global_shortcuts is not None:
            self._global_shortcuts.unregister_shortcut_handler(self)
        self._global_shortcuts = None

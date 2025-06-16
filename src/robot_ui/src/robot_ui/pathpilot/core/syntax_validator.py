from PySide6.QtCore import Slot
from PySide6.QtGui import QValidator
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class SyntaxValidator(QValidator):
    """
    Validates if a (code) string has correct Python syntax.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def validateFull(self, s, pos):
        try:
            compile(s, '', 'eval')
            state = QValidator.Acceptable
        except SyntaxError:
            state = QValidator.Invalid

        return state, s, pos

    @Slot(str, int, result=bool)
    def validate(self, s, pos):
        state, s, pos = self.validateFull(s, pos)
        return state == QValidator.Acceptable

    def fixup(self, s):
        return s

    def locale(self):
        return super().locale()

    def setLocale(self, locale):
        super().setLocale(locale)

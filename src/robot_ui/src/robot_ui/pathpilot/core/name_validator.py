import re

from PySide6.QtCore import Slot, Property, Signal
from PySide6.QtGui import QValidator
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class NameValidator(QValidator):
    """
    Validates a string based on existing names and a regex rule.
    """

    namesChanged = Signal()
    ignoredNameChanged = Signal(str)
    defaultPrefixChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._regex = re.compile(r'^[a-zA-Z_][A-Za-z0-9_]*$')
        self._names = []
        self._ignored_name = ''
        self._default_prefix = ''

    @Property('QStringList', notify=namesChanged)
    def names(self):
        """
        List of already existing names.
        :return: list of names
        """
        return self._names

    @names.setter
    def names(self, new_names):
        if new_names == self._names:
            return
        self._names = new_names
        self.namesChanged.emit()

    @Property(str, notify=ignoredNameChanged)
    def ignoredName(self):
        """
        Name which shall be ignored when comparing the existing names with the
        new input.
        :return: ignored name
        """
        return self._ignored_name

    @ignoredName.setter
    def ignoredName(self, name):
        if name == self._ignored_name:
            return
        self._ignored_name = name
        self.ignoredNameChanged.emit(name)

    @Property(str, notify=defaultPrefixChanged)
    def defaultPrefix(self):
        """
        The default prefix to be used for generating new names.
        :return: default prefix
        """
        return self._default_prefix

    @defaultPrefix.setter
    def defaultPrefix(self, value):
        if value == self._default_prefix:
            return
        self._default_prefix = value
        self.defaultPrefixChanged.emit(value)

    def validateFull(self, s, pos):
        valid = self._regex.match(s)
        state = QValidator.Acceptable if valid else QValidator.Invalid

        if state == QValidator.Acceptable:
            for name in self.names:
                if name == s and name != self._ignored_name:
                    state = QValidator.Invalid
                    break

        return state, s, pos

    @Slot(str, int, result=bool)
    def validate(self, s, pos):
        state, s, pos = self.validateFull(s, pos)
        return state == QValidator.Acceptable

    @Slot(result=str)
    def generateDefaultName(self):
        """
        Generates a new default name recommendation.
        :return: new default name
        """
        names = set(self.names)
        current = 1
        while True:
            name = f'{self._default_prefix}{current}'
            if name not in names:
                return name
            current += 1

    def fixup(self, s):
        return s

    def locale(self):
        return super().locale()

    def setLocale(self, locale):
        super().setLocale(locale)

from PySide6.QtCore import (
    QObject,
    QUrl,
    Signal,
    Property,
    Slot,
    QCoreApplication,
    QTranslator,
    QLocale,
)


class Translator(QObject):
    translationsPathChanged = Signal(QUrl)
    applicationNameChanged = Signal(str)

    def __init__(self, path=QUrl(), name='', engine=None, parent=None):
        super().__init__(parent)

        self._translations_path = path
        self._application_name = name
        self._translator = QTranslator()
        self._engine = engine

        self.translationsPathChanged.connect(self._update_translation)
        self.applicationNameChanged.connect(self._update_translation)

        self._update_translation()

    @Property(QUrl, notify=translationsPathChanged)
    def translationsPath(self):
        return self._translations_path

    @translationsPath.setter
    def translationsPath(self, value):
        if value == self._translations_path:
            return
        self._translations_path = value
        self.translationsPathChanged.emit(value)

    @Property(str, notify=applicationNameChanged)
    def applicationName(self):
        return self._application_name

    @applicationName.setter
    def applicationName(self, value):
        if value == self._application_name:
            return
        self._application_name = value
        self.applicationNameChanged.emit(value)

    @Slot()
    def _update_translation(self):
        if self._translations_path.isLocalFile():
            path = self._translations_path.toLocalFile()
        else:
            path = self._translations_path.toString()
            if path.startswith('qrc'):
                path = ':' + path[6:]

        name = self._application_name.lower()
        name = name.replace(' ', '')

        if path == '':
            return

        QCoreApplication.removeTranslator(self._translator)
        if self._translator.load(QLocale(), name, '_', path):
            QCoreApplication.installTranslator(self._translator)
            if self._engine:
                self._engine.retranslate()

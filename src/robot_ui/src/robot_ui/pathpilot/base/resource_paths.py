import os

from PySide6.QtCore import QObject, QUrl, Property
from PySide6.QtQml import QmlElement, QmlSingleton

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
RESOURCE_PATH = os.path.realpath(os.path.join(MODULE_PATH, '../../res'))
ICON_PATH = os.path.join(RESOURCE_PATH, 'icons')
FONT_PATH = os.path.join(RESOURCE_PATH, 'fonts')
STL_PATH = os.path.join(RESOURCE_PATH, '3d')
CONVERSATIONAL_PLUGIN_PATH = os.path.realpath(
    os.path.join(MODULE_PATH, '../conversational/plugins')
)
USER_PLUGIN_PATH = os.path.realpath(os.path.join(MODULE_PATH, '../../plugins'))
PROGRAM_TEMPLATE_PATH = os.path.realpath(
    os.path.join(MODULE_PATH, '../robot/program/templates')
)
TOOL_TIP_IMAGE_PATH = os.path.join(ICON_PATH, 'tooltips')
TRANSLATIONS_PATH = RESOURCE_PATH

QML_IMPORT_NAME = 'pathpilot.base'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class ResourcePaths(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._icon_path = QUrl.fromLocalFile(ICON_PATH)
        self._font_path = QUrl.fromLocalFile(FONT_PATH)
        self._conversational_plugin_path = QUrl.fromLocalFile(
            CONVERSATIONAL_PLUGIN_PATH
        )
        self._user_plugin_path = QUrl.fromLocalFile(USER_PLUGIN_PATH)
        self._program_template_path = QUrl.fromLocalFile(PROGRAM_TEMPLATE_PATH)
        self._translations_path = QUrl.fromLocalFile(TRANSLATIONS_PATH)

    @Property(QUrl, constant=True)
    def iconPath(self):
        return self._icon_path

    @Property(QUrl, constant=True)
    def fontPath(self):
        return self._font_path

    @Property(QUrl, constant=True)
    def userPluginPath(self):
        return self._user_plugin_path

    @Property(QUrl, constant=True)
    def conversationalPluginPath(self):
        return self._conversational_plugin_path

    @Property(QUrl, constant=True)
    def programTemplatePath(self):
        return self._program_template_path

    @Property(QUrl, constant=True)
    def translationsPath(self):
        return self._translations_path

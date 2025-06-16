import os

from PySide6.QtCore import QObject, Property
from PySide6.QtQml import QmlElement, QmlSingleton

import rospkg

QML_IMPORT_NAME = 'pathpilot.development'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class DevelopmentPaths(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        rospack = rospkg.RosPack()

        self._program_path = os.path.join(
            rospack.get_path('robot_command'), 'examples', 'programs'
        )

    @Property(str, constant=True)
    def programPath(self):
        return self._program_path

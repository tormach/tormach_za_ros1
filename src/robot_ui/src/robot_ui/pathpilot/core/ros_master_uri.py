import os

from PySide6.QtCore import QObject, Property
from PySide6.QtQml import QmlElement, QmlSingleton

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class RosMasterURI(QObject):
    """Interface for querying and displaying the `ROS_MASTER_URI`."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._ros_master_uri = os.getenv('ROS_MASTER_URI', None)

    @Property(str, constant=True)
    def ros_master_uri(self) -> str:
        return self._ros_master_uri or ''

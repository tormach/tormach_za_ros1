from PySide6.QtCore import QObject, Signal, Property
from PySide6.QtQml import QmlElement, QmlUncreatable
from rosgraph_msgs.msg import Log

from .logging import LogSeverityLevel


QML_IMPORT_NAME = 'pathpilot.logging'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("MessageLoggerFilter is not creatable from QML")
class MessageLoggerFilter(QObject):
    nodesChanged = Signal('QStringList')
    severityThresholdChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._nodes = []
        self._severity_threshold = LogSeverityLevel.Debug

    @Property('QStringList', notify=nodesChanged)
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        if value == self._nodes:
            return
        self._nodes = value
        self.nodesChanged.emit(value)

    @Property(int, notify=severityThresholdChanged)
    def severityThreshold(self):
        return self._severity_threshold

    @severityThreshold.setter
    def severityThreshold(self, value):
        if value == self._severity_threshold:
            return
        self._severity_threshold = LogSeverityLevel(value)
        self.severityThresholdChanged.emit(value)

    def filter_message(self, message: Log):
        if self._nodes and message.name not in self._nodes:
            return False

        return message.level >= self._severity_threshold

from PySide6.QtQml import QQmlEngine, QmlElement, qmlContext
from PySide6.QtCore import Property, Signal

from .. import Pose
from .frames import Frames

QML_IMPORT_NAME = 'pathpilot.robot.frame'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ToolFrames(Frames):
    interactiveMarkerOffsetChanged = Signal()

    def __init__(self, namespace='tool_frames', parent=None):
        super().__init__(namespace, parent)

    def _start(self):
        super()._start()
        self.interactiveMarkerOffsetChanged.emit()
        self.activeFramePoseChanged.connect(self.interactiveMarkerOffsetChanged)

    @Property(Pose, notify=interactiveMarkerOffsetChanged)
    def interactiveMarkerOffset(self):
        pose = Pose.from_euler_list(self.activeFramePose)
        if context := qmlContext(self):
            pose.setParent(context)
            QQmlEngine.setObjectOwnership(pose, QQmlEngine.JavaScriptOwnership)
        return pose

import rospy
from math import log10
from PySide6.QtQml import QJSValue
from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtQml import QPyQmlParserStatus, QmlElement, QmlUncreatable

from robot_frame import FrameClient

from ...qt_helpers import MultiSlot
from .. import Pose

QML_IMPORT_NAME = 'pathpilot.robot.frame'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlUncreatable()
@QmlElement
class Frames(QPyQmlParserStatus):
    namespaceChanged = Signal(str)
    activeFrameChanged = Signal(str)
    activeFrameFrameChanged = Signal(str)
    framesChanged = Signal()
    frameNamesChanged = Signal()
    activeFramePoseChanged = Signal()
    positionToleranceChanged = Signal(float)
    orientationToleranceChanged = Signal(float)

    NUM_AXES = 6
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(self, namespace='frames', parent=None):
        super().__init__(parent)

        self._namespace = namespace
        self._client = None
        self._position_tolerance = Pose.POSITION_TOLERANCE
        self._orientation_tolerance = Pose.ORIENTATION_TOLERANCE
        self._position_precision = 0
        self._orientation_precision = 0
        self._update_frame_precision()

        self.positionToleranceChanged.connect(self._update_frame_precision)
        self.orientationToleranceChanged.connect(self._update_frame_precision)

    @property
    def frames(self):
        if not self._client:
            return {}
        return self._client.frames

    @Property(str, notify=namespaceChanged)
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        if value == self._namespace:
            return
        self._namespace = value
        self.namespaceChanged.emit(value)

    @Property(str, notify=activeFrameChanged)
    def activeFrame(self):
        if not self._client:
            return ""
        return self._client.active_frame

    @activeFrame.setter
    def activeFrame(self, value):
        if not self._client:
            return
        if value == self._client.active_frame:
            return
        self._client.change_frame(value)

    @Property(str, notify=activeFrameFrameChanged)
    def activeFrameFrame(self):
        if not self._client:
            return "world"
        return self._client.active_frame_frame

    @Property(list, notify=activeFramePoseChanged)
    def activeFramePose(self):
        if not self._client:
            return [0, 0, 0, 0, 0, 0]
        active_frame = self._client.active_frame
        frame = self.frames.get(active_frame, {})
        return frame.get('pose', [0, 0, 0, 0, 0, 0])

    @Property('QStringList', notify=frameNamesChanged)
    def frameNames(self):
        if not self._client:
            return []
        return list(sorted(self.frames.keys()))

    @Property(float, notify=positionToleranceChanged)
    def positionTolerance(self):
        return self._position_tolerance

    @positionTolerance.setter
    def positionTolerance(self, value):
        if value == self._position_tolerance:
            return
        self._position_tolerance = value
        self.positionToleranceChanged.emit(value)

    @Property(float, notify=orientationToleranceChanged)
    def orientationTolerance(self):
        return self._orientation_tolerance

    @orientationTolerance.setter
    def orientationTolerance(self, value):
        if value == self._orientation_tolerance:
            return
        self._orientation_tolerance = value
        self.orientationToleranceChanged.emit(value)

    @MultiSlot(str, [str, list, Pose], [None, QJSValue, dict])
    def setFrame(self, name, pose, data=None):
        data = data.toVariant() if isinstance(data, QJSValue) else data
        if isinstance(pose, str):
            pose = self._read_pose_string(pose)
            self._client.set_frame(name, pose, data)
        elif isinstance(pose, list):
            pose = pose
            self._client.set_frame(name, pose, data)
        elif isinstance(pose, Pose):
            self._client.set_frame(name, pose.toEulerAngles(), data)
        else:
            raise ValueError(f"Type not supported: {pose}")

    @Slot(str)
    def deleteFrame(self, name):
        self._client.delete_frame(name)

    @Slot()
    def clearFrames(self):
        self._client.clear_frames()

    @Slot(str, result=list)
    def getFramePose(self, name):
        if not self._client:
            return [0, 0, 0, 0, 0, 0]
        frame = self.frames.get(name, {})
        return frame.get('pose', [0, 0, 0, 0, 0, 0])

    @Slot(str, int, float)
    def setFrameAxis(self, name, axis, value):
        if name not in self.frames:
            rospy.logerr(f'Frame with name {name} not defined')
            return
        if not 0 <= axis < self.NUM_AXES:
            rospy.logerr(f'Axis value must be between 0 and {self.NUM_AXES}')
            return
        pose = self.frames[name]['pose'][:]
        pose[axis] = value
        self._client.set_frame(name, pose)

    def classBegin(self):
        pass

    def componentComplete(self):
        self._start()

    def _start(self):
        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._client = FrameClient(
            self._namespace, subscribe=True, timeout=wait_timeout_s
        )
        self._client.active_frame_changed.append(self.activeFrameChanged.emit)
        self._client.frames_changed.append(self.framesChanged.emit)
        self._client.frames_changed.append(self.frameNamesChanged.emit)
        self._client.frames_changed.append(self.activeFramePoseChanged.emit)
        self.activeFrameChanged.emit(self._client.active_frame)
        self.framesChanged.emit()
        self.frameNamesChanged.emit()
        self.activeFramePoseChanged.emit()
        self.activeFrameChanged.connect(self.activeFramePoseChanged)
        self.activeFrameChanged.connect(self.activeFrameFrameChanged)

    @staticmethod
    def _read_pose_string(pose):
        stripped = pose.strip()
        if stripped[0] != '[' and stripped[-1] == ']':
            raise ValueError('Not a pose string')
        nums = [float(i) for i in stripped[1:-1].split(',')]
        if len(nums) != 6:
            raise ValueError('Not a pose string')
        return nums

    @Slot()
    def _update_frame_precision(self):
        self._position_precision = round(log10(10.0 / self._position_tolerance))
        self._orientation_precision = round(
            log10(10.0 / self._orientation_tolerance)
        )

    def _normalize_frame_pose(self, pose):
        return [round(n, self._position_precision) for n in pose[:3]] + [
            round(n, self._orientation_precision) for n in pose[3:]
        ]

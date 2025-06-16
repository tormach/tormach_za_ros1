from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor

from PySide6.QtCore import QObject, Slot, Signal, Property
from PySide6.QtQml import QJSValue, QmlElement


from robot_jog import InteractiveMoveClient

from ...qt_helpers import MultiSlot, ensure_cleanup


QML_IMPORT_NAME = 'pathpilot.robot.jog'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class InteractiveMoveClientInheritanceAdapter(InteractiveMoveClient):
    """allows super inheritance from QObject"""

    def __init__(self, **_kw):
        super().__init__()


@QmlElement
class InteractiveMove(QObject, InteractiveMoveClientInheritanceAdapter):
    activeChanged = Signal(bool)
    completedChanged = Signal(bool)
    failedChanged = Signal(bool)
    targetIsCurrentChanged = Signal(bool)
    isReachableChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._is_reachable = False
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._futures = []

        ensure_cleanup(self._shutdown)

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._active

    @Property(bool, notify=completedChanged)
    def completed(self):
        return self._completed

    @Property(bool, notify=failedChanged)
    def failed(self):
        return self._failed

    @Property(bool, notify=targetIsCurrentChanged)
    def targetIsCurrent(self):
        return self._target_is_current

    @Property(bool, notify=isReachableChanged)
    def isReachable(self):
        return self._is_reachable

    @Slot()
    def start(self):
        super().start()

    @Slot()
    def stop(self):
        super().stop()

    @MultiSlot(list, list, [None, str], result=bool)
    def setOffsetPoseTarget(self, axes, values, frame_id=''):
        axes = axes.toVariant() if isinstance(axes, QJSValue) else axes
        values = values.toVariant() if isinstance(values, QJSValue) else values
        success = self.set_offset_pose_target(axes, values, frame_id)
        self.targetIsCurrentChanged.emit(self._target_is_current)
        return success

    @MultiSlot(list, list, [None, str], result=bool)
    def setAbsolutePoseTarget(self, axes, values, frame_id=''):
        axes = axes.toVariant() if isinstance(axes, QJSValue) else axes
        values = values.toVariant() if isinstance(values, QJSValue) else values
        success = self.set_absolute_pose_target(axes, values, frame_id)
        self.targetIsCurrentChanged.emit(self._target_is_current)
        return success

    @MultiSlot(list, list, [None, str], result=bool)
    def setContinuousPoseTarget(self, axes, values, frame_id=''):
        axes = axes.toVariant() if isinstance(axes, QJSValue) else axes
        values = values.toVariant() if isinstance(values, QJSValue) else values
        success = self.set_continuous_pose_target(axes, values, frame_id)
        self.targetIsCurrentChanged.emit(self._target_is_current)
        return success

    @MultiSlot(list, list, [None, str])
    def checkOffsetPoseTargetReachable(self, axes, values, frame_id=''):
        axes = axes.toVariant() if isinstance(axes, QJSValue) else axes
        values = values.toVariant() if isinstance(values, QJSValue) else values
        if len(self._futures) > 1:
            future = self._futures.pop()
            future.cancel()
        future = self._executor.submit(
            self.check_offset_pose_target_reachable, axes, values, frame_id
        )
        self._futures.append(future)
        future.add_done_callback(self._on_reachable_check_completed)

    @MultiSlot(list, list, [None, str])
    def checkAbsolutePoseTargetReachable(self, axes, values, frame_id=''):
        axes = axes.toVariant() if isinstance(axes, QJSValue) else axes
        values = values.toVariant() if isinstance(values, QJSValue) else values
        if len(self._futures) > 1:
            future = self._futures.pop()
            future.cancel()
        future = self._executor.submit(
            self.check_absolute_pose_target_reachable, axes, values, frame_id
        )
        self._futures.append(future)
        future.add_done_callback(self._on_reachable_check_completed)

    @Slot(list, list, result=bool)
    def setOffsetJointsTarget(self, joints, values):
        joints = joints.toVariant() if isinstance(joints, QJSValue) else joints
        values = values.toVariant() if isinstance(values, QJSValue) else values
        success = self.set_offset_joints_target(joints, values)
        self.targetIsCurrentChanged.emit(self._target_is_current)
        return success

    @Slot(list, list, result=bool)
    def setAbsoluteJointsTarget(self, joints, values):
        joints = joints.toVariant() if isinstance(joints, QJSValue) else joints
        values = values.toVariant() if isinstance(values, QJSValue) else values
        success = self.set_absolute_joints_target(joints, values)
        self.targetIsCurrentChanged.emit(self._target_is_current)
        return success

    @Slot(list, list, result=bool)
    def setContinuousJointsTarget(self, joints, values):
        joints = joints.toVariant() if isinstance(joints, QJSValue) else joints
        values = values.toVariant() if isinstance(values, QJSValue) else values
        success = self.set_continuous_joints_target(joints, values)
        self.targetIsCurrentChanged.emit(self._target_is_current)
        return success

    def _on_jog_active_received(self, msg):
        super()._on_jog_active_received(msg)
        self.activeChanged.emit(self._active)

    def _on_jog_failed_received(self, msg):
        super()._on_jog_failed_received(msg)
        self.failedChanged.emit(self._failed)

    def _on_jog_completed_received(self, msg):
        super()._on_jog_completed_received(msg)
        self.completedChanged.emit(self._completed)

    def _on_reachable_check_completed(self, future: Future):
        try:
            self._futures.remove(future)
        except ValueError:
            return  # future was cancelled
        reachable = future.result()
        if reachable is not self._is_reachable:
            self._is_reachable = reachable
            self.isReachableChanged.emit(self._is_reachable)
        self.targetIsCurrentChanged.emit(self._target_is_current)

    @Slot()
    def _shutdown(self):
        super().shutdown()

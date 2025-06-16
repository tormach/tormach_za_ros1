import rospy
from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtQml import QmlElement


from ...qt_helpers import MultiSlot
from .frames import Frames
from .. import CartesianState
from ..pose_conversions import pose_list_to_kdl_frame, kdl_frame_to_pose_list

QML_IMPORT_NAME = 'pathpilot.robot.frame'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class UserFrames(Frames):
    cartesianStateChanged = Signal()

    def __init__(self, namespace='user_frames', parent=None):
        super().__init__(namespace, parent)
        self._cartesian_state = None

    @Property(CartesianState, notify=cartesianStateChanged)
    def cartesianState(self):
        return self._cartesian_state

    @cartesianState.setter
    def cartesianState(self, value):
        if value == self._cartesian_state:
            return
        self._cartesian_state = value
        self.cartesianStateChanged.emit()

    @Slot(str)
    def setFrameFromCurrent(self, name):
        if not self._cartesian_state:
            rospy.logerr(
                'CartesianState needs to be set before calling function'
            )
            return
        pose = self._cartesian_state.worldPose.toEulerAngles()
        self._client.set_frame(name, pose)

    @MultiSlot(int, [None, float])
    def touchOffAxis(self, axis, value=0.0):
        if self.activeFrame == "":
            rospy.logerr("No frame active, cannot touch off axis.")
            return
        if not self._cartesian_state:
            rospy.logerr(
                'CartesianState need to be set before calling function'
            )
            return
        if not 0 <= axis < self.NUM_AXES:
            rospy.logerr(f'Axis value must be between 0 and {self.NUM_AXES}')
            return
        current_pose = self._cartesian_state.pose.toEulerAngles()
        world_pose = self._cartesian_state.worldPose.toEulerAngles()
        name = self.activeFrame
        # calculate new frame
        world_f = pose_list_to_kdl_frame(world_pose)
        target_pose = current_pose[:]
        target_pose[axis] = value
        target_f = pose_list_to_kdl_frame(target_pose)
        new_frame_f = world_f * target_f.Inverse()
        new_frame = kdl_frame_to_pose_list(new_frame_f)
        new_frame = self._normalize_frame_pose(new_frame)
        # apply new frame
        self._client.set_frame(name, new_frame)

    @Slot(int)
    def resetAxis(self, axis):
        if self.activeFrame == "":
            rospy.logerr("No frame active, cannot set axis.")
            return
        if not 0 <= axis < self.NUM_AXES:
            rospy.logerr(f'Axis value must be between 0 and {self.NUM_AXES}')
            return
        current_pose = self._cartesian_state.pose.toEulerAngles()
        world_pose = self._cartesian_state.worldPose.toEulerAngles()
        name = self.activeFrame
        # calculate new frame
        world_f = pose_list_to_kdl_frame(world_pose)
        target_pose = current_pose[:]
        target_pose[axis] = world_pose[axis]
        target_f = kdl_frame_to_pose_list(target_pose)
        new_frame_f = world_f * target_f.Inverse()
        new_frame = kdl_frame_to_pose_list(new_frame_f)
        new_frame = self._normalize_frame_pose(new_frame)
        # apply new frame
        self._client.set_frame(name, new_frame)

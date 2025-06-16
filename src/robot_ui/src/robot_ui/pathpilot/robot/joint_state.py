# based on joint_state_publisher
import functools
from collections import OrderedDict

from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtQml import QQmlPropertyMap, QPyQmlParserStatus, QmlElement

import rospy
from sensor_msgs.msg import JointState as JointStateMessage

from robot_common.tools import get_param
from robot_common.joint_urdf import read_robot_description_free_joints

from ..qt_helpers import ensure_cleanup
from .joint import Joint

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class JointState(QPyQmlParserStatus):
    """
    Monitors and mirrors the robot joint state.
    """

    jointsChanged = Signal()
    readyChanged = Signal(bool)
    baseLinkChanged = Signal(str)
    jointNamePrefixChanged = Signal(str)
    positionToleranceChanged = Signal(float)

    def __init__(self, parent=None, base_link='', joint_name_prefix=''):
        super().__init__(parent)

        self._ready = False
        self._free_joints = OrderedDict()
        self._joints_ordered = []
        self._joint_positions = QQmlPropertyMap()
        self._joint_names = [f'j{i}' for i in range(1, 10)]
        self._dependent_joints = get_param("dependent_joints", {})
        self._use_mimic = get_param('use_mimic_tags', True)
        self._use_small = get_param('use_smallest_joint_limits', True)
        self._base_link = base_link
        self._joint_name_prefix = joint_name_prefix
        self._position_tolerance = Joint.POSITION_TOLERANCE

        self._zeros = get_param("zeros")

        source_list = get_param("joint_states_source_list", [])
        self._sources = []
        for source in source_list:
            sub = rospy.Subscriber(
                source, JointStateMessage, self._joint_status_update_received
            )
            self._sources.append(sub)

        ensure_cleanup(self._shutdown)

    def classBegin(self):
        pass

    def componentComplete(self):
        self._read_robot_description()
        self.baseLinkChanged.connect(self._read_robot_description)
        self.jointNamePrefixChanged.connect(self._read_robot_description)

    @Property(bool, notify=readyChanged)
    def ready(self):
        return self._ready

    @Property(list, notify=jointsChanged)
    def joints(self):
        return self._joints_ordered

    @Property(QQmlPropertyMap, constant=True)
    def jointPositions(self):
        return self._joint_positions

    @Slot(result=list)
    def jointPositionList(self):
        return [j.position for j in self._free_joints.items()]

    @Property(str, notify=baseLinkChanged)
    def baseLink(self):
        return self._base_link

    @baseLink.setter
    def baseLink(self, value):
        if value == self._base_link:
            return
        self._base_link = value
        self.baseLinkChanged.emit(value)

    @Property(str, notify=jointNamePrefixChanged)
    def jointNamePrefix(self):
        return self._joint_name_prefix

    @jointNamePrefix.setter
    def jointNamePrefix(self, value):
        if value == self._joint_name_prefix:
            return
        self._joint_name_prefix = value
        self.jointNamePrefixChanged.emit(value)

    @Property(float, notify=positionToleranceChanged)
    def positionTolerance(self):
        return self._position_tolerance

    @positionTolerance.setter
    def positionTolerance(self, value):
        if value == self._position_tolerance:
            return
        self._position_tolerance = value
        self.positionToleranceChanged.emit(value)

    def _update_joint_positions(self):
        for i, name in enumerate(self._free_joints.keys()):
            position = self._free_joints[name].position
            self._joint_positions.insert(str(i), position)
            self._joint_positions.insert(self._joint_names[i], position)

    def _update_joint_position(self, value, index):
        self._joint_positions.insert(str(index), value)
        self._joint_positions.insert(self._joint_names[index], value)

    def _joint_status_update_received(self, msg):
        for i, name in enumerate(msg.name):
            if name not in self._free_joints:
                continue

            joint = self._free_joints[name]
            joint.update_from_joint_state(
                msg, i, position_tolerance=self._position_tolerance
            )

    @Slot()
    def _read_robot_description(self):
        for key in self._joint_positions.keys():
            self._joint_positions.clear(key)

        free_joints = read_robot_description_free_joints(
            self._base_link,
            self._joint_name_prefix,
            self._use_small,
            self._use_mimic,
            self._dependent_joints,
            self._zeros,
        )

        self._free_joints.clear()
        self._joints_ordered = []
        for i, (name, j) in enumerate(free_joints.items()):
            joint = Joint(
                minimum=j.minimum,
                maximum=j.maximum,
                zero=j.zero,
                continuous=(j.type_ == 'continuous'),
                position=j.zero,
                velocity=0.0,
                effort=0.0,
            )
            joint.positionChanged.connect(
                functools.partial(
                    self._update_joint_position,
                    index=i,
                )
            )
            self._free_joints[name] = joint
            self._joints_ordered.append(joint)

        self.jointsChanged.emit()
        self._update_joint_positions()
        self._ready = True
        self.readyChanged.emit(True)

    @Slot()
    def _shutdown(self):
        for sub in self._sources:
            sub.unregister()

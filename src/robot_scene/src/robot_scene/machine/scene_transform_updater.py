from machinetalk.protobuf.status_pb2 import (
    LINEAR_UNITS_INCH,
    LINEAR_UNITS_MM,
    LINEAR_UNITS_CM,
    ANGULAR_UNITS_DEGREES,
    ANGULAR_UNITS_GRAD,
)
from math import radians, pi

import rospy
from tf.transformations import quaternion_from_euler

from ..scene_transform_updater_base import (
    SceneTransformUpdaterBase,
)


class SceneTransformUpdater(SceneTransformUpdaterBase):
    def __init__(self, ns=''):
        super().__init__(ns)

    def add_robot(self, description, status, node):
        self._update_base_joint(description, node)
        self._update_moving_joints(description, status)
        self._publish_transforms(description)
        self._add_meshes(description)

    def update_robot(self, description, status, node):
        self._update_base_joint(description, node)
        self._update_moving_joints(description, status)
        self._publish_transforms(description)
        self._update_meshes(description)

    def remove_robot(self, description):
        self._remove_meshes(description)

    def stop(self):
        pass

    @staticmethod
    def _update_base_joint(description, node):
        joint = description.base_joint
        offset = node.get('pose', None)
        if not offset or len(offset) != 6:
            rospy.logwarn(f"Offset for node {node['name']} is incorrect.")
            return
        joint.translation = offset[:3]
        joint.rotation = quaternion_from_euler(*offset[3:])

    @staticmethod
    def _update_moving_joints(description, status):
        actual_position = status.motion.actual_position
        axis_mask = status.config.axis_mask

        axis_names = ('x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w')
        axes = {name for i, name in enumerate(axis_names) if 2**i & axis_mask}
        for axis in axes:
            position = getattr(actual_position, axis)
            joint = description.joints.get(
                f'{description.namespace}{axis}_joint', None
            )
            if not joint:
                continue
            if joint.type == 'prismatic':
                if status.config.linear_units == LINEAR_UNITS_INCH:
                    position = position * 25.4 / 1000.0
                elif status.config.linear_units == LINEAR_UNITS_MM:
                    position /= 1000.0
                elif status.config.linear_units == LINEAR_UNITS_CM:
                    position /= 10.0
                joint.translation = [n * position for n in joint.axis]
            elif joint.type == 'revolute':
                if status.config.angular_units == ANGULAR_UNITS_DEGREES:
                    position = radians(position)
                elif status.config.angular_units == ANGULAR_UNITS_GRAD:
                    position = position * pi / 200
                joint.rotation = quaternion_from_euler(
                    *(n * position for n in joint.axis)
                )
            elif joint.type != 'fixed':
                rospy.logwarn(
                    f"Can't update unsupported joint type {joint.type}"
                )

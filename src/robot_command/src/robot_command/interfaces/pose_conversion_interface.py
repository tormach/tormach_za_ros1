import rospy
from tf2_kdl import transform_to_kdl
from tf_conversions import posemath

from ..rpl import Pose
from ..interfaces import (
    ConfigInterfaceSingleton,
    UserFrameInterfaceSingleton,
    ToolFrameInterfaceSingleton,
)


class PoseConversionInterface:
    DEFAULT_WAIT_TIMEOUT_S = 10.0

    def __init__(self):
        # Singletons to handle lookups
        self._config = ConfigInterfaceSingleton()
        self._user_frames = UserFrameInterfaceSingleton()
        self._tool_frames = ToolFrameInterfaceSingleton()
        self.tool_reference_frame = rospy.get_param(
            'moveit/tool_reference_frame', 'tool0'
        )
        self.pose_reference_frame = rospy.get_param(
            'moveit/pose_reference_frame', 'world'
        )

    def shutdown(self):
        pass  # nothing to do

    # Helper functions to compose for transform conversions

    def to_ros_pose(self, pose_in):
        ros_units_pose = pose_in.to_ros_units(
            self._config.linear_unit, self._config.angular_unit
        )
        return ros_units_pose.to_ros_pose()

    def from_ros_pose(self, ros_pose):
        pose = Pose.from_ros_pose(ros_pose)
        return pose.from_ros_units(
            self._config.linear_unit,
            self._config.angular_unit,
        )

    def convert_ros_global_to_ros_work(self, ros_pose) -> Pose:
        active_user_frame = self._user_frames.active_frame
        if active_user_frame:
            transform = self._user_frames.get_transform(
                active_user_frame, inverse=True
            )
            if transform:
                ros_pose = posemath.toMsg(
                    transform_to_kdl(transform) * posemath.fromMsg(ros_pose)
                )
        return ros_pose

    def convert_ros_work_to_ros_tool(self, ros_pose) -> Pose:
        active_tool_frame = self._tool_frames.active_frame
        if active_tool_frame:
            transform = self._tool_frames.get_transform(active_tool_frame)
            if transform:
                ros_pose = posemath.toMsg(
                    posemath.fromMsg(ros_pose) * transform_to_kdl(transform)
                )
        return ros_pose

    # User-facing functions to do full pose conversions

    def convert_global_to_tool_pose(self, global_pose_in) -> Pose:
        return self.from_ros_pose(
            self.convert_ros_work_to_ros_tool(
                self.convert_ros_global_to_ros_work(
                    self.to_ros_pose(global_pose_in)
                )
            )
        )


class PoseConversionInterfaceSingleton:
    """
    Singleton interface class query poses from joint states.
    """

    _instance = None

    def __init__(self):
        if not PoseConversionInterfaceSingleton._instance:
            PoseConversionInterfaceSingleton._instance = (
                PoseConversionInterface()
            )

    def __getattr__(self, item):
        return getattr(self._instance, item)

    def __setattr__(self, key, value):
        return setattr(self._instance, key, value)

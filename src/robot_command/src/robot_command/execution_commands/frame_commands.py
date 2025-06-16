from typing import Optional

import rospy

from ..rpl import Command, Pose
from ..interfaces import (
    UserFrameInterfaceSingleton,
    GlobalWaypointInterfaceSingleton,
    ConfigInterfaceSingleton,
    ToolFrameInterfaceSingleton,
)


class SetFrameCommand(Command):
    name = 'set_frame'
    NO_FRAME_NAME = 'world'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(
        self,
        name,
        pose=None,
        position=None,
        orientation=None,
    ):
        super().__init__()
        self._frames = self.FRAME_INTERFACE()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()
        self._config = ConfigInterfaceSingleton()
        if not isinstance(name, str):
            raise TypeError('Frame name must be specified as first argument.')
        if name == self.NO_FRAME_NAME:
            raise TypeError(f'Frame name must not be "{self.NO_FRAME_NAME}".')
        pose = self._get_pose(pose, message='second')
        position = self._get_pose(position, message='position')
        orientation = self._get_pose(orientation, message='orientation')
        if pose:
            self.pose = pose.copy()
        if position is not None:
            pose = Pose() if pose is None else pose
            pose.x = position.x
            pose.y = position.y
            pose.z = position.z
        if orientation is not None:
            pose = Pose() if pose is None else pose
            pose.a = orientation.a
            pose.b = orientation.b
            pose.c = orientation.c

        self.frame_name = name
        self.pose = pose

    def _get_pose(self, pose, message):
        if pose is None:
            return None

        if isinstance(pose, str):
            pose = self._global_waypoints.get_global_waypoint(pose)

        if not isinstance(pose, Pose):
            raise TypeError(
                f'{self.name} requires Pose type as {message} argument'
            )

        return pose

    def execute(self) -> None:
        rospy.logdebug(f'executing {self.name}: {self.frame_name} {self.pose}')
        if self.pose:
            pose = self.pose.to_ros_units(
                self._config.linear_unit, self._config.angular_unit
            )
        else:
            pose = None  # clear frame
        self._frames.set_frame(self.frame_name, pose)

    def __str__(self):
        return f'{self.name}: {self.frame_name} {self.pose}'


class GetFrameCommand(Command):
    name = 'get_frame'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(self, name):
        super().__init__()
        self._config = ConfigInterfaceSingleton()
        self._frame = self.FRAME_INTERFACE()
        if not isinstance(name, str):
            raise TypeError('Frame name must be specified as first argument.')

        if name not in self._frame.frames.keys():
            print(self._frame.frames.keys())
            raise TypeError(f"Frame with name {name} does not exist.")

        self.frame_name = name

    def execute(self) -> Optional[Pose]:
        rospy.logdebug(f'executing {self.name}: {self.frame_name}')
        pose = self._frame.get_frame(self.frame_name)
        if pose:
            return pose.from_ros_units(
                self._config.linear_unit,
                self._config.angular_unit,
            )
        else:
            return None

    def __str__(self):
        return f'{self.name}: {self.frame_name}'


class ChangeFrameCommand(Command):
    name = 'change_frame'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(self, name):
        super().__init__()
        self._frames = self.FRAME_INTERFACE()
        if not (name is None or isinstance(name, str)):
            raise TypeError("Frame name must be specified as first argument.")

        if not name:
            name = None
        elif name not in self._frames.frames.keys():
            raise TypeError(f"Frame with name {name} does not exist.")

        self.tool_name = name

    def execute(self) -> None:
        rospy.logdebug(f'executing {self.name}: {self.tool_name}')
        self._frames.change_frame(self.tool_name)

    def __str__(self):
        return f'{self.name}: {self.tool_name}'


class GetActiveUserFrameCommand(Command):
    name = 'get_active_user_frame'
    FRAME_INTERFACE = UserFrameInterfaceSingleton

    def __init__(self):
        super().__init__()
        self._config = ConfigInterfaceSingleton()
        self._frame = self.FRAME_INTERFACE()

        self.active_frame_name = self._frame.active_frame

    def execute(self) -> str:
        rospy.logdebug(f'executing {self.name}: {self.active_frame_name}')
        if self.active_frame_name:
            return self.active_frame_name
        else:
            return ""

    def __str__(self):
        return f'{self.name}: {self.active_frame_name}'


class GetActiveToolFrameCommand(Command):
    name = 'get_active_tool_frame'
    FRAME_INTERFACE = ToolFrameInterfaceSingleton

    def __init__(self):
        super().__init__()
        self._config = ConfigInterfaceSingleton()
        self._frame = self.FRAME_INTERFACE()

        self.active_frame_name = self._frame.active_frame

    def execute(self) -> str:
        rospy.logdebug(f'executing {self.name}: {self.active_frame_name}')
        if self.active_frame_name:
            return self.active_frame_name
        else:
            return ""

    def __str__(self):
        return f'{self.name}: {self.active_frame_name}'

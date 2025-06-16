import rospy

from ..rpl import ScopedCommand, Pose
from ..interfaces import (
    UserFrameInterfaceSingleton,
    GlobalWaypointInterfaceSingleton,
    ConfigInterfaceSingleton,
)


class UserFrame(ScopedCommand):
    name = 'user_frame'

    def __init__(self, pose=None, position=None, orientation=None, world=False):
        """
        Scoped frame command. Applies a user frame temporarily on top of the
        currently active user frame.

        The scoped frame command can be used to automatically switch the active
        frame back to a previous state when the scope is left. Scoped frames
        can be nested. Scoped frames are temporary and do not have a name.

        :param pose: The frame pose.
        :param position: A pose from which the position is used for the frame.
        :param orientation: A pose from which the orientation is used for the frame.
        :param world: If set to True the frame is absolute.

        **Examples**

        .. code-block:: python

            with user_frame(p[0, 100, 0, 90, 20, 0]): # creates a temporary frame and activates it
                movel(Pose(x=10)) # move x by 10 starting from the frame
                # the active frame automatically reset when the scope is left
        """
        super().__init__()
        self._frames = UserFrameInterfaceSingleton()
        self._global_waypoints = GlobalWaypointInterfaceSingleton()
        self._config = ConfigInterfaceSingleton()
        pose = self._get_pose(pose, message='first')
        position = self._get_pose(position, message='position')
        orientation = self._get_pose(orientation, message='orientation')
        if pose:
            pose = pose.copy()
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

        self.pose = pose
        self.world = world
        self._previous_frame = None
        self._name = ""

    def _get_pose(self, pose, message):
        if pose is None:
            return None

        if isinstance(pose, str):
            pose = self._global_waypoints.get_global_waypoint(pose)

        if not isinstance(pose, Pose):
            raise TypeError(
                '{} requires Pose type as {} argument'.format(
                    self.name, message
                )
            )

        return pose

    def __enter__(self):
        rospy.logdebug(f'entering frame: {self.pose}')
        active_frame = self._frames.active_frame
        self._previous_frame = active_frame
        self._name = active_frame + "+" if active_frame else "_stack"
        self._frames.set_frame(
            self._name,
            self.pose.to_ros_units(
                self._config.linear_unit, self._config.angular_unit
            ),
            frame=None if self.world else active_frame,
            temporary=True,
        )
        self._frames.change_frame(self._name)

    def __exit__(self, type_, value, traceback):
        rospy.logdebug(f'exiting frame: {self.pose}')
        self._frames.change_frame(self._previous_frame)
        self._frames.set_frame(self._name, None, temporary=True)

    def __str__(self):
        return f'frame: {self.pose}'

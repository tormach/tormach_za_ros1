from __future__ import annotations
import numbers
from typing import Union, Optional, List

import attr
from pint.util import SharedRegistryObject

from tf.transformations import euler_from_quaternion, quaternion_from_euler
from geometry_msgs.msg import Pose as RosPose, PoseStamped
from PyKDL import Frame, Rotation, Vector

from robot_command.rpl.units import ureg, force_units
from movej_ik_server.arm_configs import JointConfig, arm_config_strings


class PoseFactory:
    """
    The PoseFactory class helps constructing Pose object using a shorthand
    notation. In the robot program it can be accessed using the ``p[]``
    shortcut or the ``p()`` shortcut which supports keyword arguments.

    **Examples**

    .. code-block:: python

        waypoint_1 = p[202.73, 750.08, 91.75, 6.63, 53.21, "table"]  # captured with table user frame
        waypoint_2 = p(y=10.0, frame="table")  # all other coordinate values are 0.0 per default.
    """

    MESSAGE = 'Exactly 6, 7, 8, or 9 values [X,Y,Z,A,B,C,(frame),(arm_config),(rev_count)] required to create a pose.'

    def __getitem__(self, values):
        final_values = []
        try:
            elements = len(values)
        except TypeError as e:
            raise ValueError(self.MESSAGE) from e
        if elements == 6:
            coords = values
            final_values = list(coords)
        elif elements == 7:
            coords = values[:6]
            conf_frame_candidate = values[6]
            if isinstance(conf_frame_candidate, str):
                frame = conf_frame_candidate
                if frame.upper() in arm_config_strings:
                    raise ValueError(
                        "Cannot use arm config string as frame name."
                    )
                final_values = list(coords) + [frame]
            elif isinstance(conf_frame_candidate, JointConfig):
                frame = ""
                conf = conf_frame_candidate
                final_values = list(coords) + [frame, conf]
            else:
                raise ValueError(self.MESSAGE)

        elif elements == 8:
            coords = values[:6]
            # frame = values[6]
            conf_frame_candidate = values[6]
            conf_rev_candidate = values[7]
            if isinstance(conf_frame_candidate, str) and isinstance(
                conf_rev_candidate, JointConfig
            ):
                frame = conf_frame_candidate
                if frame.upper() in arm_config_strings:
                    raise ValueError(
                        "Cannot use arm config string as frame name."
                    )
                conf = conf_rev_candidate
                final_values = list(coords) + [frame, conf]
            elif isinstance(conf_frame_candidate, JointConfig) and isinstance(
                conf_rev_candidate, numbers.Integral
            ):
                frame = ""
                conf = conf_frame_candidate
                rev = conf_rev_candidate
                final_values = list(coords) + [frame, conf, rev]
            else:
                raise ValueError(self.MESSAGE)

        elif elements == 9:
            coords = values[:6]
            frame = values[6]
            if frame.upper() in arm_config_strings:
                raise ValueError("Cannot use arm config string as frame name.")
            conf = values[7]
            rev = values[8]
            if (
                isinstance(frame, str)
                and isinstance(conf, JointConfig)
                and isinstance(rev, numbers.Integral)
            ):
                final_values = list(coords) + [frame, conf, rev]
        else:
            raise ValueError(
                "Inalid type or number of arugments passed to PoseFactory.__getitem__"
            )

        if not all(
            isinstance(v, (numbers.Number, ureg.Quantity)) for v in coords
        ):
            raise ValueError(self.MESSAGE)

        return Pose(*final_values)

    def __call__(self, *args, **kwargs):
        if args and len(args) < 6:
            raise ValueError(
                "Shorthand notation requires at least 6 coordinate values"
                " or keyword arguments only."
            )
        return Pose(*args, **kwargs)


# TODO: add arm config
@attr.s(slots=True)
class Pose:
    """
    A robot pose consists of XYZ position ABC orientation parameters.

    Optionally, an frame frame can be recorded with a waypoint.

    **Examples**

    .. code-block:: python

        waypoint_1 = Pose(483.21, 34.21, 21.59, 42.03, 71.14)
        waypoint_2 = Pose(a=0.543) # all other coordinate values are 0.0 per default.
    """

    x = attr.ib(default=0.0, type=Union[numbers.Number, ureg.Quantity])
    y = attr.ib(default=0.0, type=Union[numbers.Number, ureg.Quantity])
    z = attr.ib(default=0.0, type=Union[numbers.Number, ureg.Quantity])
    a = attr.ib(default=0.0, type=Union[numbers.Number, ureg.Quantity])
    b = attr.ib(default=0.0, type=Union[numbers.Number, ureg.Quantity])
    c = attr.ib(default=0.0, type=Union[numbers.Number, ureg.Quantity])
    frame = attr.ib(default="", type=str)
    conf = attr.ib(default=None, type=JointConfig)
    rev = attr.ib(default=None, type=Union[numbers.Number, ureg.Quantity])
    _obj_name = attr.ib(init=False, default='Pose')

    def copy(self) -> Pose:
        """
        Creates a copy of the pose object.

        :return: A copy of the pose.
        """
        return attr.evolve(self)

    def to_list(self) -> List[float]:
        """
        Convert the pose to a list of the coordinates.
        :return: List of the six coordinates.
        """
        return [self.x, self.y, self.z, self.a, self.b, self.c]

    # def get_conf(self) -> str:
    #     return self.conf

    @staticmethod
    def from_list(pose_list: List[float]) -> Pose:
        """
        Creates a new pose object from a list of coordinates.

        :param pose_list: List of the six coordinates.
        :return: New pose object.
        """
        return Pose(*pose_list)

    @staticmethod
    def from_ros_pose(pose: Union[RosPose, PoseStamped]) -> Pose:
        """
        Converts a ROS native pose to a pose object.

        :param pose: The ROS stamped pose.
        :return: New pose object.
        """
        if isinstance(pose, PoseStamped):
            p = pose.pose.position
            o = pose.pose.orientation
        else:
            p = pose.position
            o = pose.orientation
        quaternion = [o.x, o.y, o.z, o.w]
        euler = euler_from_quaternion(
            quaternion, axes='sxyz'
        )  # static/fixed frame XYZ
        return Pose(x=p.x, y=p.y, z=p.z, a=euler[0], b=euler[1], c=euler[2])

    def to_ros_pose(self) -> RosPose:
        """
        Converts the pose object to a native ROS pose.

        :return: ROS pose.
        """
        pose = RosPose()
        pose.position.x = self.x
        pose.position.y = self.y
        pose.position.z = self.z
        q = quaternion_from_euler(self.a, self.b, self.c, axes='sxyz')
        pose.orientation.x = q[0]
        pose.orientation.y = q[1]
        pose.orientation.z = q[2]
        pose.orientation.w = q[3]
        return pose

    def to_kdl_frame(self) -> Frame:
        """
        Converts the pose object to a KDL frame.

        :return: KDL frame.
        """
        # note convert XYZ static to ZYX body rotation -> flip C and A
        return Frame(
            Rotation.EulerZYX(self.c, self.b, self.a),
            Vector(self.x, self.y, self.z),
        )

    @staticmethod
    def from_kdl_frame(frame: Frame) -> Pose:
        """
        Converts a KDL frame to a pose object.

        :param frame: KDL frame.
        :return: New pose object.
        """
        o = frame.M.GetEulerZYX()
        return Pose(frame.p[0], frame.p[1], frame.p[2], o[2], o[1], o[0])

    def with_units(
        self,
        linear_unit: Optional[Union[str, SharedRegistryObject]] = None,
        angular_unit: Optional[Union[str, SharedRegistryObject]] = None,
    ) -> Pose:
        """
        Adds a unit type to all coordinates of the pose. The defaults are the
        native ROS units. In case a coordinate already has units, the unit type
        is converted accordingly.

        :param linear_unit: Unit type for linear coordinates.
        :param angular_unit: Unit type for angular coordinates.
        :return: The resulting pose.
        """
        if linear_unit is None:
            linear_unit = ureg.m
        if angular_unit is None:
            angular_unit = ureg.rad
        return Pose(
            x=force_units(self.x, linear_unit),
            y=force_units(self.y, linear_unit),
            z=force_units(self.z, linear_unit),
            a=force_units(self.a, angular_unit),
            b=force_units(self.b, angular_unit),
            c=force_units(self.c, angular_unit),
            frame=self.frame,
        )

    def without_units(
        self,
        linear_unit: Optional[Union[str, SharedRegistryObject]] = None,
        angular_unit: Optional[Union[str, SharedRegistryObject]] = None,
    ) -> Pose:
        """
        Removes units from the coordinates if any. If no unit type is specified
        ROS units are assumed.

        :param linear_unit: Unit type for linear coordinates.
        :param angular_unit: Unit type for angular coordinates.
        :return: The resulting pose.
        """
        if linear_unit is None:
            linear_unit = ureg.m
        if angular_unit is None:
            angular_unit = ureg.rad
        return Pose(
            x=force_units(self.x, linear_unit).magnitude,
            y=force_units(self.y, linear_unit).magnitude,
            z=force_units(self.z, linear_unit).magnitude,
            a=force_units(self.a, angular_unit).magnitude,
            b=force_units(self.b, angular_unit).magnitude,
            c=force_units(self.c, angular_unit).magnitude,
            frame=self.frame,
        )

    def to_ros_units(
        self,
        linear_unit: Optional[Union[str, SharedRegistryObject]] = None,
        angular_unit: Optional[Union[str, SharedRegistryObject]] = None,
    ) -> Pose:
        """
        Converts the pose to native ROS units, removing the unit type if any.
        This is useful if you want to send the resulting data to a ROS service.

        :param linear_unit: Unit type for linear coordinates.
        :param angular_unit: Unit type for angular coordinates.
        :return: The resulting pose.
        """
        if linear_unit is None:
            linear_unit = ureg.m
        if angular_unit is None:
            angular_unit = ureg.rad
        return Pose(
            x=force_units(self.x, linear_unit).to(ureg.m).magnitude,
            y=force_units(self.y, linear_unit).to(ureg.m).magnitude,
            z=force_units(self.z, linear_unit).to(ureg.m).magnitude,
            a=force_units(self.a, angular_unit).to(ureg.rad).magnitude,
            b=force_units(self.b, angular_unit).to(ureg.rad).magnitude,
            c=force_units(self.c, angular_unit).to(ureg.rad).magnitude,
            frame=self.frame,
            conf=self.conf,
            rev=self.rev,
        )

    def from_ros_units(
        self,
        linear_unit: Optional[Union[str, SharedRegistryObject]] = None,
        angular_unit: Optional[Union[str, SharedRegistryObject]] = None,
    ):
        """
        Converts the pose from native ROS units to the target units, removing
        the unit type.

        :param linear_unit: Unit type for linear coordinates.
        :param angular_unit: Unit type for angular coordinates.
        :return: The resulting pose.
        """
        if linear_unit is None:
            linear_unit = ureg.m
        if angular_unit is None:
            angular_unit = ureg.rad
        return Pose(
            x=force_units(self.x, ureg.m).to(linear_unit).magnitude,
            y=force_units(self.y, ureg.m).to(linear_unit).magnitude,
            z=force_units(self.z, ureg.m).to(linear_unit).magnitude,
            a=force_units(self.a, ureg.rad).to(angular_unit).magnitude,
            b=force_units(self.b, ureg.rad).to(angular_unit).magnitude,
            c=force_units(self.c, ureg.rad).to(angular_unit).magnitude,
            frame=self.frame,
            conf=self.conf,
            rev=self.rev,
        )

    def inverse(self) -> Pose:
        """
        Creates the inverse of the pose. Useful for calculating frames.

        :return: New pose object.
        """
        return Pose.from_kdl_frame(self.to_kdl_frame().Inverse())

    def __mul__(self, other: Pose) -> Pose:
        """
        Use KDL frame multiplication to apply a frame to a pose.

        :param other: Other pose.
        :return: New pose object.

        .. code-block:: python

            new_wp = Pose(x=10) * waypoint_1 # translates waypoint_1 by x=10
            old_wp = Pose(x=10).inverse() * new_wp # translates new_wp back
        """
        return Pose.from_kdl_frame(self.to_kdl_frame() * other.to_kdl_frame())

from math import isnan

from ..rpl import (
    Pose,
    RobotProgramError,
)

from PyKDL import Rotation, Vector
import numpy as np


def unit_vector(v):
    return v / np.sqrt(v.dot(v))


def calculate_plane_origin(a: Pose, b: Pose, c: Pose) -> Pose:
    """
    Calculates the plane origin based on 3 waypoints that lie on a plane.
    :param a: Origin of the plane.
    :param b: A point that lies on the X-axis of the plane.
    :param c: A point that lies in the direction of the Y-axis of the plane.
    :return: Origin pose of the constructed plane.
    """
    ab = unit_vector(np.array([b.x - a.x, b.y - a.y, b.z - a.z]))
    ac = unit_vector(np.array([c.x - a.x, c.y - a.y, c.z - a.z]))
    norm = np.cross(ab, ac)
    vec2 = np.cross(norm, ab)

    rot_c, rot_b, rot_a = Rotation(
        Vector(ab[0], ab[1], ab[2]),
        Vector(vec2[0], vec2[1], vec2[2]),
        Vector(norm[0], norm[1], norm[2]),
    ).GetEulerZYX()
    if isnan(rot_a) or isnan(rot_b) or isnan(rot_c):
        raise RobotProgramError("Calculating plane orientation failed")
    return Pose(x=a.x, y=a.y, z=a.z, a=rot_a, b=rot_b, c=rot_c)


def calculate_user_frame_3(
    origin_wp: Pose, x_axis_wp: Pose, y_axis_wp: Pose
) -> Pose:
    """
    Calculates the user frame origin pose based on 3 waypoints that lie on a plane.

    The angular unit of all input poses must be in radians.

    :param origin_wp: Origin of the plane.
    :param x_axis_wp: A waypoint that lies on the X-axis of the plane.
    :param y_axis_wp: A waypoint that lies in the direction of the Y-axis of the plane.
    :return: Origin waypoint of the constructed user frame.
    """
    return calculate_plane_origin(origin_wp, x_axis_wp, y_axis_wp)


def calculate_user_frame_4(
    origin_wp: Pose, x_axis_wp: Pose, y_axis_wp: Pose, position_wp: Pose
) -> Pose:
    """
    Calculates the user frame origin pose based on 3 waypoints that lie on a plane
    and one additional waypoint which is used to define the origin location.

    The angular unit of all input poses must be in radians.

    :param origin_wp: Origin of the plane.
    :param x_axis_wp: A waypoint that lies on the X-axis of the plane.
    :param y_axis_wp: A waypoint that lies in the direction of the Y-axis of the plane.
    :param position_wp: Origin location of the new user frame.
    :return: Origin waypoint of the constructed user frame.
    """
    frame_origin_wp = calculate_plane_origin(origin_wp, x_axis_wp, y_axis_wp)
    frame_origin_wp.x = position_wp.x
    frame_origin_wp.y = position_wp.y
    frame_origin_wp.z = position_wp.z
    return frame_origin_wp

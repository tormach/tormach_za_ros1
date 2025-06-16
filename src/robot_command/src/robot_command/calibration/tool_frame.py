from ..rpl import Pose, RobotProgramError


def calc_sphere_center(p1: Pose, p2: Pose, p3: Pose, p4: Pose) -> Pose:
    """
    Calculates the center of sphere in 3D space.

    :param p1: Point 1 on the sphere.
    :param p2: Point 2 on the sphere.
    :param p3: Point 3 on the sphere.
    :param p4: Point 4 on the sphere.
    :return: Sphere origin point.
    """
    x1, y1, z1 = p1.x, p1.y, p1.z
    x2, y2, z2 = p2.x, p2.y, p2.z
    x3, y3, z3 = p3.x, p3.y, p3.z
    x4, y4, z4 = p4.x, p4.y, p4.z
    try:
        # fmt: off
        u = ((1/2)*(-((-y1 + y4)*((-x1 + x4)*(-z2 + z4) - (-x2 + x4)*(-z1 + z4)) - (-z1 + z4)*((-x1 + x4)*(-y2 + y4) - (-x2 + x4)*(-y1 + y4)))*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(x3**2 - x4**2 + y3**2 - y4**2 + z3**2 - z4**2) - (x3 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(x2**2 - x4**2 + y2**2 - y4**2 + z2**2 - z4**2) - (x2 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2))) + ((-y1 + y4)*((-x1 + x4)*(-x2**2 + x4**2 - y2**2 + y4**2 - z2**2 + z4**2) - (-x2 + x4)*(-x1**2 + x4**2 - y1**2 + y4**2 - z1**2 + z4**2)) - ((-x1 + x4)*(-y2 + y4) - (-x2 + x4)*(-y1 + y4))*(-x1**2 + x4**2 - y1**2 + y4**2 - z1**2 + z4**2))*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(z3 - z4) - (x3 - x4)*(z1 - z4)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(z2 - z4) - (x2 - x4)*(z1 - z4))))/((x1 - x4)*((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(z3 - z4) - (x3 - x4)*(z1 - z4)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(z2 - z4) - (x2 - x4)*(z1 - z4)))))  # noqa: E226
        v = ((1/2)*(-((x1 - x4)*(z2 - z4) - (x2 - x4)*(z1 - z4))*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(x3**2 - x4**2 + y3**2 - y4**2 + z3**2 - z4**2) - (x3 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(x2**2 - x4**2 + y2**2 - y4**2 + z2**2 - z4**2) - (x2 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2))) + ((x1 - x4)*(x2**2 - x4**2 + y2**2 - y4**2 + z2**2 - z4**2) - (x2 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2))*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(z3 - z4) - (x3 - x4)*(z1 - z4)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(z2 - z4) - (x2 - x4)*(z1 - z4))))/(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(z3 - z4) - (x3 - x4)*(z1 - z4)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(z2 - z4) - (x2 - x4)*(z1 - z4)))))  # noqa: E226
        w = ((1/2)*(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(x3**2 - x4**2 + y3**2 - y4**2 + z3**2 - z4**2) - (x3 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(x2**2 - x4**2 + y2**2 - y4**2 + z2**2 - z4**2) - (x2 - x4)*(x1**2 - x4**2 + y1**2 - y4**2 + z1**2 - z4**2)))/(((x1 - x4)*(y2 - y4) - (x2 - x4)*(y1 - y4))*((x1 - x4)*(z3 - z4) - (x3 - x4)*(z1 - z4)) - ((x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4))*((x1 - x4)*(z2 - z4) - (x2 - x4)*(z1 - z4))))  # noqa: E226
        # fmt: on
    except ZeroDivisionError:
        raise RobotProgramError()

    return Pose(u, v, w)


def calculate_tool_frame_4(wp1: Pose, wp2: Pose, wp3: Pose, wp4: Pose) -> Pose:
    """
    Calculate the XYZ coordinates of the tool frame using 4 waypoints using the
    center of sphere method.

    :param wp1: Waypoint 1
    :param wp2: Waypoint 2
    :param wp3: Waypoint 3
    :param wp4: Waypoint 4
    :return: The tool frame pose containing the XYZ tool frame.
    """
    sphere_center = calc_sphere_center(wp1, wp2, wp3, wp4)
    wpc = wp1.copy()
    wpc.x, wpc.y, wpc.z = sphere_center.x, sphere_center.y, sphere_center.z
    return Pose.from_kdl_frame(
        wp1.to_kdl_frame().Inverse() * wpc.to_kdl_frame()
    )

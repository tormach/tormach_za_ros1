from robot_command.rpl import *
set_units("mm", "deg", "s")

# Replace these with appropriate positions for your test setup
probe_center_guess_pose = p[-25.98, 545.74, 147.0, 0, 0, 0]
probe_retract_pose = p[-25.98, 545.74, 175.0, 0, 0, 0]
import rospy
import random


def probe_rectangular_pocket(
    probe_center_guess_pose, length_x_mm, width_y_mm, v=0.005, v_retract=0.05
):
    """
    Simple demo of a program to probe a rectangular, axis-aligned pocket.
    Assumes that the initial guess pose is at an appropriate Z height to make
    contact with all 4 sides. This routine moves in +X, -X, +Y, -Y until probe
    makes contact, then uses the resulting contact poses to compute the XY
    center.
    """
    movel(probe_center_guess_pose, v=v_retract)
    with user_frame(probe_center_guess_pose):
        x_plus_pose = p[length_x_mm, 0, 0, 0, 0, 0]
        x_minus_pose = p[-length_x_mm, 0, 0, 0, 0, 0]
        y_plus_pose = p[0, width_y_mm, 0, 0, 0, 0]
        y_minus_pose = p[0, -width_y_mm, 0, 0, 0, 0]
        res_xplus = probel(x_plus_pose, v=v, v_retract=v_retract)
        res_xminus = probel(x_minus_pose, v=v, v_retract=v_retract)
        res_yplus = probel(y_plus_pose, v=v, v_retract=v_retract)
        res_yminus = probel(y_minus_pose, v=v, v_retract=v_retract)
        rospy.logwarn(
            f"Got contacts: {res_xplus.x}, {res_xminus.x}, {res_yplus.y}, {res_yminus.y}"
        )
        x_mid = (res_xplus.x + res_xminus.x) / 2.0
        y_mid = (res_yplus.y + res_yminus.y) / 2.0
        rospy.logwarn(f"Got center x = {x_mid}, y = {y_mid}")

    result_xy_center = probe_center_guess_pose.copy()
    result_xy_center.x = x_mid
    result_xy_center.y = y_mid
    # NOTE: must move without user frames applied (result from probe is always in global coordinates)
    movel(result_xy_center, v=v)
    return result_xy_center


def main():
    csv_data = [
        '',
        'start_x,start_y,start_z,start_a,start_b,start_c, center_x,center_y',
    ]
    try:
        x_start_window = 20
        y_start_window = 10
        for k in range(10):
            start_pose = probe_center_guess_pose.copy()
            start_pose.x += (random.random() - 0.5) * x_start_window
            start_pose.y += (random.random() - 0.5) * y_start_window
            movel(probe_retract_pose, v=0.05)
            center_pos = probe_rectangular_pocket(start_pose, 50, 50)
            csv_data.append(
                ', '.join([str(x) for x in start_pose.to_list()])
                + ', '.join([str(x) for x in center_pos.to_list()[0:2]])
            )
            rospy.logwarn(f"Got center pose: {center_pos}")
        # Attempt to probe above the work (should error out)
        try:
            center_pos2 = probe_rectangular_pocket(probe_retract_pose, 50, 50)
            rospy.logwarn(f"Got center pose: {center_pos2}")
        except ProbeFailedError as e:
            rospy.logwarn(f"got expected ProbeFailedError: {e}")
    finally:
        rospy.loginfo('\n'.join(csv_data))

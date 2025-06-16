import rospy

from robot_command.calibration import (
    calculate_user_frame_3,
    calculate_user_frame_4,
)
from robot_command.rpl import (
    get_param,
    set_param,
    pause,
    get_pose,
    sleep,
    get_units,
    set_user_frame,
    RobotProgramError,
)


def main():
    waypoints = [None] * 4
    for i in range(4):
        set_param(f"waypoint{i+1}_set", False)
    set_param("origin_wp_set", False)
    set_param("x_axis_wp_set", False)
    set_param("y_axis_wp_set", False)
    set_param("teach_waypoint", 0)
    set_param("waypoints_ready", False)
    set_param("accept_waypoints", False)
    set_param("calibration_method", 3)

    while True:
        pause(active=True)

        teach_waypoint_nr = get_param("teach_waypoint")
        if teach_waypoint_nr:
            pose = get_pose(apply_user_frame=False)
            pose = pose.to_ros_units(*get_units())
            waypoints[teach_waypoint_nr - 1] = pose
            set_param(f"waypoint{teach_waypoint_nr}_set", True)

            calibration_method = get_param("calibration_method")
            if sum(w is not None for w in waypoints) == calibration_method:
                set_param("waypoints_ready", True)

            set_param("teach_waypoint", 0)

        if get_param("accept_waypoints"):
            frame_name = get_param("frame_name")
            calibration_method = get_param("calibration_method")
            origin_wp = waypoints[0]
            x_axis_wp = waypoints[1]
            y_axis_wp = waypoints[2]
            try:
                if calibration_method == 3:
                    frame_pose = calculate_user_frame_3(
                        origin_wp, x_axis_wp, y_axis_wp
                    )
                elif calibration_method == 4:
                    position_wp = waypoints[3]
                    frame_pose = calculate_user_frame_4(
                        origin_wp, x_axis_wp, y_axis_wp, position_wp
                    )
                else:
                    raise RobotProgramError("Unsupported calibration method")
            except RobotProgramError:
                rospy.logerr(
                    "Calculating user frame failed, please verify your input waypoints."
                )
            else:
                frame_pose = frame_pose.from_ros_units(*get_units())
                set_user_frame(frame_name, frame_pose)
            exit()

        sleep(0.2)

import rospy

from robot_command.calibration import calculate_tool_frame_4
from robot_command.rpl import (
    get_param,
    set_param,
    pause,
    get_pose,
    sleep,
    set_tool_frame,
    get_units,
    RobotProgramError,
)


def main():
    waypoints = [None] * 4
    for i in range(4):
        set_param(f"waypoint{i+1}_set", False)
    set_param("teach_waypoint", 0)
    set_param("waypoints_ready", False)
    set_param("accept_waypoints", False)
    set_param("calibration_method", 4)

    while True:
        pause(active=True)

        teach_waypoint_nr = get_param("teach_waypoint")
        if teach_waypoint_nr:
            pose = get_pose(apply_user_frame=False, apply_tool_frame=False)
            pose = pose.to_ros_units(*get_units())
            waypoints[teach_waypoint_nr - 1] = pose
            set_param(f"waypoint{teach_waypoint_nr}_set", True)

            calibration_method = get_param("calibration_method")
            if sum(w is not None for w in waypoints) == calibration_method:
                set_param("waypoints_ready", True)

            set_param("teach_waypoint", 0)

        if get_param("accept_waypoints"):
            frame_name = get_param("frame_name")
            try:
                frame_pose = calculate_tool_frame_4(*waypoints)
                frame_pose = frame_pose.from_ros_units(*get_units())
                set_tool_frame(frame_name, frame_pose)
            except RobotProgramError:
                rospy.logerr(
                    "Calculating tool frame failed, please verify your input waypoints."
                )
            exit()

        sleep(0.2)

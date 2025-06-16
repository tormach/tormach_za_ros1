import sys
import rospy
from copy import deepcopy

from moveit_commander import (
    RobotCommander,
    PlanningSceneInterface,
    roscpp_initialize,
    roscpp_shutdown,
    MoveGroupCommander,
)
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Pose
import moveit_msgs


def main():
    roscpp_initialize(sys.argv)
    rospy.init_node('moveit_py_demo', anonymous=True)

    display_trajectory_publisher = rospy.Publisher(
        '/move_group/display_planned_path',
        moveit_msgs.msg.DisplayTrajectory,
        queue_size=20,
    )

    robot = RobotCommander()
    manipulator = MoveGroupCommander('manipulator')
    # Allow replanning to increase the odds of a solution
    manipulator.allow_replanning(True)
    # Set the robot reference frame
    manipulator.set_pose_reference_frame('base_link')
    # Allow some leeway in position(meters) and orientation (radians)
    manipulator.set_goal_position_tolerance(0.001)
    manipulator.set_goal_orientation_tolerance(0.01)

    end_effector_link = manipulator.get_end_effector_link()
    start_pose = manipulator.get_current_pose(end_effector_link).pose
    print(start_pose)

    master_plan = manipulator.plan()

    target = Pose()
    target.position.x = 0.2
    target.position.y = 0.2
    target.position.z = 1.2
    manipulator.set_pose_target(target, end_effector_link)
    plan1 = manipulator.plan()
    # manipulator.start_program(plan1)

    waypoints = []

    # first orient gripper and move forward (+x)
    wpose = deepcopy(target)
    print(wpose)
    # wpose.orientation.w = 1.0
    wpose.position.x = 0.3
    waypoints.append(deepcopy(wpose))

    # second move down
    wpose.position.z = 1.10
    waypoints.append(deepcopy(wpose))

    # third move to the side
    wpose.position.y = 0.3
    waypoints.append(deepcopy(wpose))

    (plan3, fraction) = manipulator.compute_cartesian_path(
        waypoints, 0.01, 0.0  # waypoints to follow  # eef_step
    )  # jump_threshold
    print(plan3)

    print(dir(master_plan.joint_trajectory))
    master_plan.joint_trajectory += plan1.joint_trajectory
    master_plan.joint_trajectory += plan3.joint_trajectory
    # master_plan.joint_trajectory.points += plan1.joint_trajectory.points
    # master_plan.joint_trajectory.points += plan3.joint_trajectory.points
    manipulator.start_program(master_plan)

    return

    display_trajectory = moveit_msgs.msg.DisplayTrajectory()
    display_trajectory.trajectory_start = robot.get_current_state()
    display_trajectory.trajectory.append(plan1)
    display_trajectory_publisher.publish(display_trajectory)

    manipulator.go()
    target.position.z -= 0.1
    manipulator.set_pose_target(target, end_effector_link)
    manipulator.go()

    joints = manipulator.get_current_joint_values()
    joints[0] = 0.5
    manipulator.set_joint_value_target(joints)
    manipulator.go()

    print(joints)

    roscpp_shutdown()


if __name__ == '__main__':
    main()

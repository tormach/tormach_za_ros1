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
    rospy.init_node('moveit_py_demo', anonymous=True)
    roscpp_initialize(sys.argv)

    manipulator = MoveGroupCommander('manipulator')
    manipulator.allow_replanning(True)
    manipulator.set_pose_reference_frame('base')
    manipulator.set_goal_position_tolerance(0.001)
    manipulator.set_goal_orientation_tolerance(0.01)
    rospy.loginfo('init complete')

    end_effector_link = manipulator.get_end_effector_link()
    start_pose = manipulator.get_current_pose(end_effector_link).pose
    print(start_pose)

    target = Pose()
    target.position.x = 0.2
    target.position.y = 0.2
    target.position.z = 1.2
    manipulator.set_pose_target(target, end_effector_link)
    # plan = manipulator.plan()
    rospy.loginfo('go')
    manipulator.go()

    roscpp_shutdown()


if __name__ == '__main__':
    main()

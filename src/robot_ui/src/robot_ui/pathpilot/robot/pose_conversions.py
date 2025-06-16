from PyKDL import Frame, Rotation, Vector
from geometry_msgs.msg import Pose as RosPose, PoseStamped


def pose_list_to_kdl_frame(pose):
    return Frame(
        Rotation.EulerZYX(pose[5], pose[4], pose[3]),
        Vector(pose[0], pose[1], pose[2]),
    )


def kdl_frame_to_pose_list(frame):
    pose = []
    pose[0:3] = frame.p[0], frame.p[1], frame.p[2]
    pose[3:6] = reversed(frame.M.GetEulerZYX())
    return pose


def ros_pose_to_kdl_frame(pose):
    if isinstance(pose, PoseStamped):
        p = pose.pose.position
        o = pose.pose.orientation
    else:
        p = pose.position
        o = pose.orientation
    return Frame(Rotation.Quaternion(o.x, o.y, o.z, o.w), Vector(p.x, p.y, p.z))


def kdl_frame_to_ros_pose(frame):
    pose = RosPose()
    pose.position.x = frame.p[0]
    pose.position.y = frame.p[1]
    pose.position.z = frame.p[2]
    q = frame.M.GetQuaternion()
    pose.orientation.x = q[0]
    pose.orientation.y = q[1]
    pose.orientation.z = q[2]
    pose.orientation.w = q[3]
    return pose


def pose_list_to_ros_pose(pose):
    return kdl_frame_to_ros_pose(pose_list_to_kdl_frame(pose))


def ros_pose_to_pose_list(pose):
    return kdl_frame_to_pose_list(ros_pose_to_kdl_frame(pose))

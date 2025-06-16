from geometry_msgs.msg import PoseStamped
from numpy.ma import arange


class BoxPoseGenerator:
    def __init__(self, base_frame):
        self._base_frame = base_frame

    def generate_poses(self, start_point, end_point, step_size):
        poses = []
        for x in arange(start_point.x, end_point.x + step_size, step_size):
            for y in arange(start_point.y, end_point.y + step_size, step_size):
                for z in arange(
                    start_point.z, end_point.z + step_size, step_size
                ):
                    pose_stamped = PoseStamped()
                    pose_stamped.header.frame_id = self._base_frame
                    pose = pose_stamped.pose
                    pose.position.x = x
                    pose.position.y = y
                    pose.position.z = z
                    pose.orientation.x = 0.0
                    pose.orientation.y = 0.0
                    pose.orientation.z = 0.0
                    pose.orientation.w = 1.0
                    poses.append(pose_stamped)
        return poses

    def shutdown(self):
        pass

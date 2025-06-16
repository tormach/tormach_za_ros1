from math import sqrt

from geometry_msgs.msg import PoseStamped
from numpy.ma import arange


class SpherePoseGenerator:
    def __init__(self, base_frame):
        self._base_frame = base_frame

    def generate_poses(self, center_point, radius, step_size):
        poses = []
        for x in arange(
            center_point.x - radius,
            center_point.x + radius + step_size,
            step_size,
        ):
            for y in arange(
                center_point.y - radius,
                center_point.y + radius + step_size,
                step_size,
            ):
                for z in arange(
                    center_point.z - radius,
                    center_point.z + radius + step_size,
                    step_size,
                ):
                    dist = sqrt(
                        pow(center_point.x - x, 2)
                        + pow(center_point.y - y, 2)
                        + pow(center_point.z - z, 2)
                    )
                    if dist > radius:
                        continue
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

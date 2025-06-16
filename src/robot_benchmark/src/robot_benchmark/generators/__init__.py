from enum import Enum

from .box_pose_generator import BoxPoseGenerator  # noqa: F401
from .random_pose_generator import RandomPoseGenerator  # noqa: F401
from .sphere_pose_generator import SpherePoseGenerator  # noqa: F401


class Generators(Enum):
    RANDOM = 0
    BOX = 1
    SPHERE = 2

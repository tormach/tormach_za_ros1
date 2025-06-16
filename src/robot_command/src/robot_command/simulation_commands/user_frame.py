from ..rpl import ScopedCommand, Pose


class UserFrame(ScopedCommand):
    name = 'user_frame'

    def __init__(self, pose=None, position=None, orientation=None, world=False):
        super().__init__()
        if pose:
            pose = pose.copy()
        if position is not None:
            pose = Pose() if pose is None else pose
            pose.x = position.x
            pose.y = position.y
            pose.z = position.z
        if orientation is not None:
            pose = Pose() if pose is None else pose
            pose.a = orientation.a
            pose.b = orientation.b
            pose.c = orientation.c

        self.pose = pose
        self.world = world

    def __enter__(self):
        print(f'entering frame: {self.pose}')

    def __exit__(self, type_, value, traceback):
        print(f'exiting frame: {self.pose}')

    def __str__(self):
        return f'frame: {self.pose}'

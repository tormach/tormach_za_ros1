from ..rpl import Command, Pose


class SetUserFrame(Command):
    name = 'set_user_frame'

    def __init__(self, name, pose=None, position=None, orientation=None):
        super().__init__()
        if not isinstance(name, str):
            raise TypeError('Frame name must be specified as first argument.')
        if name == 'world':
            raise TypeError('Frame name must not be "world".')
        if pose:
            self.pose = pose.copy()
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

        self.frame_name = name
        self.pose = pose

    def execute(self):
        print(f'executing {self.name}: {self.frame_name} {self.pose}')

    def __str__(self):
        return f'{self.name}: {self.frame_name} {self.pose}'

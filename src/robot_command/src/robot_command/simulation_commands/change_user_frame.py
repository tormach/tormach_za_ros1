from ..rpl import Command


class ChangeUserFrame(Command):
    name = 'change_user_frame'

    def __init__(self, name):
        super().__init__()
        if not (name is None or isinstance(name, str)):
            raise TypeError("Frame name must be specified as first argument.")

        self.frame_name = name

    def execute(self):
        print(f'executing {self.name}: {self.frame_name}')

    def __str__(self):
        return f'{self.name}: {self.frame_name}'

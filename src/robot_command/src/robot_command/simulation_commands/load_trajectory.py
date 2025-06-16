from ..rpl import Command


class LoadTrajectory(Command):
    name = 'load_trajectory'

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def execute(self):
        print(f'executing load trajectory command: {self.file_path}')
        return None

    def __str__(self):
        return f'{self.name}: file_path={self.file_path}'

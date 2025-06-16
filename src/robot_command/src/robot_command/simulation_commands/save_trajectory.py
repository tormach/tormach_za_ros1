from trajectory_msgs.msg import JointTrajectory

from ..rpl import Command


class SaveTrajectory(Command):
    name = 'save_trajectory'

    def __init__(self, file_path: str, trajectory: JointTrajectory):
        super().__init__()
        self.file_path = file_path
        self.trajectory = trajectory

    def execute(self):
        print(f'executing {self.name}: {self.file_path}')

    def __str__(self):
        return (
            f'{self.name}: file_path={self.file_path} trajectory '
            f'len={len(self.trajectory.points)}'
        )

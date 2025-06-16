import rospy
from trajectory_msgs.msg import JointTrajectory

from ..rpl import Command
from ..rpl.trajectory import Trajectory


class SaveTrajectory(Command):
    name = 'save_trajectory'

    def __init__(self, file_path: str, trajectory: JointTrajectory):
        """
        The save trajectory command saves a joint trajectory to a CSV file.

        :param file_path: Path of the CSV file.
        :param trajectory: The joint trajectory to save.
        """
        super().__init__()
        self.file_path = file_path
        self.trajectory = trajectory

    def execute(self) -> None:
        rospy.logdebug(f'executing {self.name}')
        Trajectory.save_to_csv(self.file_path, self.trajectory)

    def __str__(self):
        return (
            f'{self.name}: file_path={self.file_path} trajectory '
            f'len={len(self.trajectory.points)}'
        )

import rospy
from trajectory_msgs.msg import JointTrajectory

from ..rpl import Command
from ..rpl.trajectory import Trajectory


class LoadTrajectory(Command):
    name = 'load_trajectory'

    def __init__(self, file_path: str):
        """
        Loads a raw joint trajectory from a CSV file and returns them in ROS format.

        :param file_path: Path of the CSV file.
        :return: A ROS joint trajectory.
        """
        super().__init__()
        self.file_path = file_path

    def execute(self) -> JointTrajectory:
        rospy.logdebug(f'executing {self.name}')
        return Trajectory.load_from_csv(self.file_path)

    def __str__(self):
        return f'{self.name}: file_path={self.file_path}'

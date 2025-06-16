from .process_launcher import ProcessLauncher
import os

from PySide6.QtCore import Slot
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class RobotUILauncher(ProcessLauncher):
    """Launches the robot_ui from launch files

    Requires passing a package name with a launch file named
    `robot_ui.launch`
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str, str)
    def configureRun(self, run_pp_ros_args: str, ros_launch_args: str) -> None:
        robot_package = os.environ.get('ROBOT_PACKAGE', None)
        if robot_package:
            self.logger.info(
                f"Determined robot package '{robot_package}' from environment"
            )
        else:
            msg = "Unable to determine robot package!"
            self.logger.fatal(msg)
            raise RuntimeError(msg)

        cmd = [
            'rosrun',
            '--debug',
            'pp_ros_launch',
            'run_pp_ros',
            run_pp_ros_args,
            'roslaunch',
            robot_package,
            'robot_ui.launch',
            ros_launch_args,
        ]
        self.logger.info("Running command '%s'" % ' '.join(cmd))
        self._executable = cmd[0]
        self._args = ' '.join(cmd[1:])

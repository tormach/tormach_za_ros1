from .subsystem import SubSystemCheck, SubSystem
import os


class EnvironmentModeCheck(SubSystemCheck):
    """Pass environment variable for older versions of TPPR:  EtherCAT or sim

    Remove in due time
    """

    name = "hardware_mode"
    fatal = False

    @classmethod
    def add_cl_args(cls, parser):
        # Base hardware modes are mutually exclusive
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "-s",
            "--sim",
            help="Run in simulated hardware mode",
            dest="hardware_mode",
            action="store_const",
            const="sim",
        )
        mode_group.add_argument(
            "-e",
            "--ethercat",
            help="Run in EtherCAT hardware mode",
            dest="hardware_mode",
            action="store_const",
            const="ethercat",
        )
        mode_group.add_argument(
            '-hm2',
            '--ethernet',
            help='Run in Ethernet HM2 hardware mode',
            dest='hardware_mode',
            action='store_const',
            const='hm2',
        )

    def run_check(self):
        return True

    def docker_run_environment(self):
        # For now, keep compatibility with older images by passing the `sim`
        # launch arg into the container as env var `HARDWARE_MODE=sim`
        if self.get_cl_arg('sim'):
            return dict(HARDWARE_MODE="sim")
        if self.get_cl_arg('hardware_mode', None) is not None:
            return dict(HARDWARE_MODE=self.get_cl_arg('hardware_mode'))
        return dict()


class RobotModelCheck(SubSystemCheck):
    """Robot model

    Checks the robot model, e.g. `za`, and robot package,
    e.g. `za6_robot`, from environment and passes into
    container environment.
    """

    name = "robot_model"

    def run_check(self):
        robot_model = os.environ.get("ROBOT_MODEL")
        robot_package = os.environ.get("ROBOT_PACKAGE")
        if robot_model is None:
            self.log_fatal("Unable to determine robot model!")
            return False
        if robot_package is None:
            self.log_fatal("Unable to determine robot package!")
            return False
        # FIXME robot model/package validity checking
        self.set_config("robot_model", robot_model)
        self.set_config("robot_package", robot_package)
        self.log_info(
            'Determined robot model "%s" and package "%s" from environment'
            % (robot_model, robot_package)
        )
        return True

    def docker_run_environment(self):
        if not self.cached_result():
            return dict()
        robot_model = self.get_config("robot_model")
        robot_package = self.get_config("robot_package")
        return dict(ROBOT_MODEL=robot_model, ROBOT_PACKAGE=robot_package)


class HWMode(SubSystem):
    name = "hardware_mode"
    check_classes = [EnvironmentModeCheck, RobotModelCheck]

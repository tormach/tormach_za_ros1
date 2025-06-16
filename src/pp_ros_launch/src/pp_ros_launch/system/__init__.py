from pp_ros_launch.config import PPROSContainerConfig
from . import (
    account,
    launcher,
    linux_system,
    docker_image,
    dbus,
    ethercat,
    ethernet,
    gpu,
    motherboard,
    user,
    workdir,
    mode,
)

from typing import Tuple, Dict, List

import logging

logger = logging.getLogger(__name__)


class SystemChecks(PPROSContainerConfig):
    """Run system checks.

    This module collects all subsystem checks into one place.
    """

    subsystem_classes = [
        launcher.Launcher,
        linux_system.LinuxSystem,
        mode.HWMode,
        dbus.Dbus,
        ethercat.EtherCAT,
        ethernet.EthernetHM2,
        gpu.GPU,
        motherboard.Motherboard,
        user.User,
        account.PathPilotHUBAccount,
        workdir.Workdir,
        docker_image.DockerImage,
    ]

    SubSystemCheckLog = subsystem_classes[0].SubSystemCheckLog

    def __init__(self, cl_args=None):
        super().__init__()
        self.init_config(cl_args)
        self.subsystems = [s() for s in self.subsystem_classes]

    @classmethod
    def clear_cache(cls):
        """Clear out cached results."""
        for s in cls.subsystem_classes:
            s.clear_cache()

    @classmethod
    def get_cache(cls):
        """Return cached result dict"""
        return cls.subsystem_classes[0].get_cache()

    @classmethod
    def add_cl_args(cls, parser):
        cls.add_cl_state_file_arg(parser)
        for c in cls.subsystem_classes:
            c.add_cl_args(parser)

    @property
    def check_results(self):
        """Return overall results for subsystem checks."""
        return all(s.check_results for s in self.subsystems)

    @property
    def check_results_nonfatal(self):
        """Return overall notfatal results for subsystem checks."""
        return all(s.check_results_nonfatal for s in self.subsystems)

    @property
    def list_failed_nonfatal(self) -> bool:
        """Return list of all failed nonfatal Subsystem checks."""
        return all(s.check_results_nonfatal for s in self.subsystems)

    def result_data(self) -> dict:
        result: dict = dict()
        for s in self.subsystems:
            srd = s.result_data()
            if srd:
                result.update({s.name: srd})
        return result

    def docker_run_environment(self):
        """Return dictionary of environment variables to set in Docker
        container.

        Gathered from subsystem test results.
        """
        env = {}
        for s in self.subsystems:
            env.update(s.docker_run_environment())
        return env

    def docker_run_volumes(self):
        """Return dictionary of volumes to bind-mount in Docker container.

        Gathered from subsystem test results.
        """
        vol = {}
        for s in self.subsystems:
            vol.update(s.docker_run_volumes())
        return vol

    def docker_run_mounts(self) -> List[Dict]:
        """Return list of mounts to mount inside the Docker container.
        Mounts are represented as a Python Dictionary with important items as specified in Docker Daemon API.

        Gathered from subsystem test results.
        """
        mounts = []
        for s in self.subsystems:
            mounts.extend(s.docker_run_mounts())
        return mounts

    def docker_run_args(self):
        """Return all arguments to run Docker container.

        Gathered from subsystem test results.
        """
        args = {}
        for s in self.subsystems:
            args.update(s.docker_run_args())
        args.update(
            dict(
                environment=self.docker_run_environment(),
                volumes=self.docker_run_volumes(),
                mounts=self.docker_run_mounts(),
            )
        )

        if self.cl_args.store_checks:
            # Write the ``docker run`` arguments to the config file
            # ``docker_run_args`` key

            # This is ugly as it will (probably) write even EtherCAT arguments when we are trying to just get SIM
            self.set_config('docker_run_args', args)
            # Actually, DO NOT write the config to the file as this should be outside the
            #           ¨¨¨¨¨¨
            # purview of this stage
            # self.write_config()

        return args

    def logs(
        self,
        info=True,
        warning=True,
        fatal=True,
        recommendation=True,
        fatal_checks_only=True,
    ):
        """Return list of log tuples reported by subsystem checks."""
        res = []
        for s in self.subsystems:
            found_fatal = False
            keepers = []
            for log in s.logs:
                if log.level == log.msg_level_fatal:
                    found_fatal = True
                if log.level == log.msg_level_info and not info:
                    continue
                if log.level == log.msg_level_warning and not warning:
                    continue
                if log.level == log.msg_level_fatal and not fatal:
                    continue
                if (
                    log.level == log.msg_level_recommendation
                    and not recommendation
                ):
                    continue
                keepers.append(log.msg)
            if fatal_checks_only and not found_fatal:
                continue
            res += keepers
        return res

    def failed_nonfatal_subsystems(self) -> list:
        return [s.name for s in self.subsystems if not s.check_results_nonfatal]

    def available_configurations(
        self,
    ) -> Tuple[Dict[str, Tuple[str, str]], Dict]:
        self.init_config()

        results: bool = self.check_results_nonfatal
        check_data: dict = self.result_data().get('EtherCAT', dict())
        configurations = {'<203': dict(), '>=203': dict()}
        status_message = {}

        ethercat_possible = True
        robotiq_possible = True

        if any(check_data.values()):
            drives620 = [0, 0]
            drives660 = [0, 0]
            hw_errors = {}

            for key, drive in check_data.get('ec_drives', dict()).items():
                drive_name = drive.get('name', 'Unknown Drive')

                drive_list = None
                if drive_name == 'Drive620':
                    drive_list = drives620
                elif drive_name == 'Drive660':
                    drive_list = drives660
                else:
                    continue

                if drive.get('error', True):
                    hw_errors.update({key: drive_name})

                    drive_list[1] = drive_list[1] + 1
                    ethercat_possible = False
                else:
                    drive_list[0] = drive_list[0] + 1

            io_boards = [0, 0]
            for key, io_board in check_data.get('general_io', dict()).items():
                if io_board.get('error', True):
                    hw_errors.update({key: io_board.get('name', 'IO board')})
                    io_boards[1] = io_boards[1] + 1
                    ethercat_possible = False
                else:
                    io_boards[0] = io_boards[0] + 1

            tools = [0, 0]
            for key, tool in check_data.get('tools', dict()).items():
                if tool.get('error', True):
                    hw_errors.update({key: tool.get('name', 'Tool')})
                    tools[1] = tools[1] + 1
                    robotiq_possible = False
                else:
                    tools[0] = tools[0] + 1

            if any(hw_errors.values()):
                status_message.update({'hardware_errors': hw_errors})

            all_drives = (
                drives620[0] + drives620[1] + drives660[0] + drives660[1]
            )

            if all_drives == 6:
                if (drives620[0] + drives620[1] != 6) and (
                    drives620[0] + drives620[1] > 0
                ):
                    ethercat_possible = False
                    status_message.update(
                        {"missing_drives_620": 6 - drives620[0] + drives620[1]}
                        if drives620[0] + drives620[1] < 6
                        else {
                            "excess_drives_620": drives620[0] + drives620[1] - 6
                        }
                    )

                if (drives660[0] + drives660[1] != 6) and (
                    drives660[0] + drives660[1] > 0
                ):
                    ethercat_possible = False
                    status_message.update(
                        {"missing_drives_660": 6 - drives660[0] + drives660[1]}
                        if drives660[0] + drives660[1] < 6
                        else {
                            "excess_drives_660": drives660[0] + drives660[1] - 6
                        }
                    )
            else:
                ethercat_possible = False

            if drives660[0] + drives660[1] == 0:
                if io_boards[0] + io_boards[1] != 1:
                    status_message.update(
                        {"missing_io_boards": 1}
                        if io_boards[0] + io_boards[1] < 1
                        else {
                            "excess_io_boards": io_boards[0] + io_boards[1] - 1
                        }
                    )
                    ethercat_possible = False

            if tools[0] + tools[1] != 1:
                if tools[0] + tools[1] > 1:
                    status_message.update(
                        {"excess_tools": tools[0] + tools[1] - 1}
                    )
                robotiq_possible = False
        else:
            ethercat_possible = False
            robotiq_possible = False

        configurations = dict()
        status_message = dict()

        # ZA6 real hardware
        if results and ethercat_possible:
            configurations["ZA6"] = ('-pc "ZA6" --ethercat', '')
            configurations["ZA6 Mastering"] = (
                '-pc "ZA6 Mastering" --ethercat',
                'mastering:=true',
            )
            if robotiq_possible:
                configurations["ZA6 with Robotiq Hand-E"] = (
                    '-pc "ZA6 with Robotiq Hand-E" --ethercat',
                    'tool:=hand_e',
                )

        # ZA6 sim
        configurations["ZA6 Simulation"] = ('-pc "ZA6 Simulation" --sim', '')

        return configurations, status_message

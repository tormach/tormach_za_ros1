from .subsystem import SubSystem, SubSystemCheck, SubSystemDockerVolumeCheck
import os


class MountWorkdir(SubSystemDockerVolumeCheck):
    """Mount the current working directory in the Docker container."""

    name = "mount_workdir"

    @property
    def path(self):
        return os.getcwd()


class RunWorkdir(SubSystemCheck):
    """Use the current working directory as the Docker container workdir."""

    name = "run_workdir"

    @property
    def path(self):
        return os.getcwd()

    def run_check(self):
        # Compute docker_run_args in the check for meaningful status
        # messages
        self.log_info("Container run workdir:  %s" % self.path)
        return True

    def docker_run_args(self):
        return dict(working_dir=self.path)


class Workdir(SubSystem):
    """Mount the current working directory in the Docker container."""

    name = "workdir"

    check_classes = [MountWorkdir, RunWorkdir]

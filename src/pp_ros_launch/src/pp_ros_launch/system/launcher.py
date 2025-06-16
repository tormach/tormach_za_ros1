from .subsystem import SubSystemDockerVolumeCheck, SubSystem
import os


class LauncherStateDirCheck(SubSystemDockerVolumeCheck):
    """Bind-mount state information directory into container

    By default, ``~/.pathpilot``.  Configuration data lives
    here.
    """

    name = "launcher_state_dir"
    absent_ok = True  # Bind-mount directory even if it doesn't exist

    @property
    def path(self):
        return os.path.dirname(self.get_state_path())

    def run_check(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        return super().run_check()


class Launcher(SubSystem):
    """Add resources to Docker container for launcher"""

    name = "launcher"

    check_classes = [LauncherStateDirCheck]

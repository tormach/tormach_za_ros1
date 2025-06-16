from .subsystem import (
    SubSystem,
    SubSystemDockerVolumeCheck,
)


class DevMountPoint(SubSystemDockerVolumeCheck):
    """Bind-mount the ``/dev`` mount-point into the Docker
    container.
    """

    name = "dev_mount_point"
    path = "/dev"

    def run_check(self):
        res = super().run_check()
        if not res:
            self.log_recommendation(
                "The /dev directory should be present on all Linux systems."
            )
        return res


class LinuxSystem(SubSystem):
    """Check the EtherCAT base system and pass into the container."""

    name = "LinuxSystem"

    check_classes = [
        DevMountPoint,
    ]

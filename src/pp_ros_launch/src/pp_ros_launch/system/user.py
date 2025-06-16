from .subsystem import SubSystem, SubSystemCheck, SubSystemDockerMountCheck
import os


class UidGidHome(SubSystemCheck):
    """Configure the user in the Docker container.

    This check sets the UID and GID of the Docker container,
    bind-mounts the user's home directory, and passes in the ``$HOME``
    environment variable.
    """

    name = "uid_gid"

    def run_check(self):
        self.set_cache("uid", os.getuid())
        self.set_cache("gid", os.getgid())
        self.set_cache("user", os.environ.get("USER"))
        self.set_cache("home", os.environ.get("HOME"))
        self.log_info(
            "User={}, UID={}, GID={}, home={}".format(
                self.get_cache('uid'),
                self.get_cache('gid'),
                self.get_cache('user'),
                self.get_cache('home'),
            )
        )
        return True

    def docker_run_environment(self):
        return dict(
            UID=str(self.get_cache('uid')),
            GID=str(self.get_cache('gid')),
            USER=str(self.get_cache('user')),
            HOME=str(self.get_cache('home')),
        )

    def docker_run_volumes(self):
        return self.docker_volume_param(self.get_cache('home'))


class UserMediaDirCheck(SubSystemDockerMountCheck):
    """Mount the user media directory into container

    By default the "/media/${USER}
    """

    name = "user_media_dir"

    @property
    def host_path(self):
        return f'/media/{os.environ.get("USER")}'

    @property
    def container_path(self):
        return f'/media/{os.environ.get("USER")}'


class User(SubSystem):
    """Configure the user in the Docker container."""

    name = "User"

    check_classes = [UidGidHome, UserMediaDirCheck]

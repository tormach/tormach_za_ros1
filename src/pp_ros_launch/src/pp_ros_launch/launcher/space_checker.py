import shutil
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

DOCKER_MINIMUM_FREE_SPACE_GB = 10


async def get_docker_root_directory():
    """This is a hack until a better solution is found.
    This solution presumes that the Docker daemon works from single mount
    (in other words, that the images, containers, volumes etc share single space)
    and by querying how much space is available for this container we get how much
    space is available for additional images
    """
    return Path('/')


def find_free_space_gb(path: Path):
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB

    mountpoint = path
    while not mountpoint.is_mount():
        mountpoint = mountpoint.parent

    free_space_gb = shutil.disk_usage(mountpoint).free / GB

    return free_space_gb


async def docker_has_enough_space() -> bool:
    return (
        find_free_space_gb(await get_docker_root_directory())
        > DOCKER_MINIMUM_FREE_SPACE_GB
    )

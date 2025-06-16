import aiodocker
import pathlib
import shutil
import asyncio
import stat
import os
import logging

from typing import Union, List


class BaseOSUpdater:
    """
    Args:
    common_path_prefix (str): Common path which is the same for both Base OS
                              system and Launcher container and should be simply
                              computable from BaseOsUpdater container via prefixing
    """

    def __init__(
        self,
        common_path_prefix: Union[str, pathlib.Path],
        storage_path: Union[str, pathlib.Path],
        repository_path_suffix: Union[str, pathlib.Path],
        install_packages: List[str],
    ):
        if isinstance(common_path_prefix, str):
            common_path_prefix = pathlib.Path(common_path_prefix)
        if isinstance(storage_path, str):
            storage_path = pathlib.Path(storage_path)
        if isinstance(repository_path_suffix, str):
            repository_path_suffix = pathlib.Path(repository_path_suffix)

        self._logger = logging.getLogger('pp_ros_launch.launcher.baseOSUpdater')

        self._common_path_prefix = common_path_prefix

        self._storage_path = storage_path

        if not (self._storage_path.exists() and self._storage_path.is_dir()):
            raise RuntimeError(
                "Path to package storage has to be a pre-existing directory!"
            )

        self._repository_path = common_path_prefix / repository_path_suffix

        if not self._repository_path.exists():
            self._repository_path.mkdir()
        if not self._repository_path.is_dir():
            raise RuntimeError(
                f'Path {self._repository_path} is not directory!'
            )

        self._base_os_prefix = pathlib.Path('/baseos')

        self._install_packages = install_packages

    def copy_new_packages(self) -> None:
        extensions = ['deb', 'ddeb']

        for extension in extensions:

            def new_packages():
                return self._storage_path.rglob(f"*.{extension}")

            def old_packages():
                return self._repository_path.rglob(f"*.{extension}")

            old_packages_names = [package.name for package in old_packages()]

            for package in new_packages():
                if package.name not in old_packages_names:
                    shutil.copy(package, self._repository_path)

    async def create_repo(self) -> None:
        """
        Trivial APT repositories are in theory DEPRECATED, however it is still
        the easiest way how to create a temporary local repository
        """
        dpkg = await asyncio.create_subprocess_exec(
            'dpkg-scanpackages',
            '-m',
            str(self._repository_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        with open(self._repository_path / 'Packages', 'wb') as packages:
            output, error = await dpkg.communicate()
            packages.write(output)

    def delete_repo(self) -> None:
        shutil.rmtree(self._repository_path, ignore_errors=True)

    async def update_base_system(self) -> None:
        entrypoint = rf"""#!/bin/bash
echo "Base OS Updater startup"

chroot {self._base_os_prefix} /bin/bash -x  <<'EOF'
export DEBIAN_FRONTEND=noninteractive

# Hack to work around the malformed file path (/tmp/apt//tmp/apt/*) problem
# when using 'file:///tmp/apt ./' like documentation recommends
echo "deb [trusted=yes] file:/// {str(self._repository_path)}/" \
    >/etc/apt/sources.list.d/tormachlocal.list

apt-get update -o Dir::Etc::sourcelist="sources.list.d/tormachlocal.list" \
    -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0";

packages=({' '.join(self._install_packages)})


for package in "${{packages[@]}}";
do
    if dpkg -s ${{package}} >/dev/null 2>&1;
    then
        echo "Package ${{package}} is already installed, trying to update.";
        apt-get --only-upgrade --assume-yes install ${{package}};
    else
        echo "Package ${{package}} is not installed, installing.";
        apt-get install --assume-yes ${{package}};
    fi;
done;

rm /etc/apt/sources.list.d/tormachlocal.list;
EOF
        """
        run_directory = self._common_path_prefix / "run"

        if not run_directory.exists():
            run_directory.mkdir()
        if not run_directory.is_dir():
            raise RuntimeError(f'Path {run_directory} is already used!')

        entrypoint_path = run_directory / "entrypoint.sh"

        with open(entrypoint_path, 'w') as ef:
            ef.write(entrypoint)

        entrypoint_path.chmod(
            stat.S_IXUSR
            | stat.S_IXOTH
            | stat.S_IXGRP
            | stat.S_IREAD
            | stat.S_IRGRP
            | stat.S_IRUSR
            | stat.S_IWUSR
            | stat.S_IWGRP
        )

        entrypoint_updater_path = (
            self._base_os_prefix / entrypoint_path.relative_to('/')
        )

        container_name = 'baseOsUpdater'
        container_config = {
            'Image': 'debian:buster',
            'Entrypoint': [str(entrypoint_updater_path)],
            'HostConfig': {'Binds': [f'/:{str(self._base_os_prefix)}']},
        }

        async with aiodocker.docker.Docker() as docker:
            try:
                container = None
                try:
                    container = await docker.containers.get(container_name)
                    self._logger.warning(
                        f"Already running container {container_name}"
                        " found, trying to delete it!"
                    )
                    running = container._container.get("State", {}).get(
                        "Running", False
                    )
                    if running:
                        await container.stop()
                    await container.delete()
                except aiodocker.exceptions.DockerError:
                    pass
                container = await docker.containers.run(
                    config=container_config,
                    name=container_name,
                )

                result_data = await container.wait()
                for log in await container.log(stdout=True, stderr=True):
                    self._logger.warning(log)

                await container.delete(force=True)

                exit_code = result_data.get('StatusCode', 100)
                if exit_code != 0:
                    self._logger.error(
                        'The PathPilot BaseOS Updater returned'
                        f'non-zero exit code: {exit_code}'
                    )

                entrypoint_path.unlink()
            except Exception as e:
                self._logger.error(
                    'Exception eccured during the main bulk'
                    f'of BaseOS system updating: {e}'
                )
                # Not really such a big error to immediately halt all operation


async def standard_update() -> bool:
    common_path_prefix = pathlib.Path(f"{os.environ['HOME']}/.pathpilot")
    storage_path = pathlib.Path("/opt/pathpilot/robot/packages/deb")
    repository_path_suffix = pathlib.Path('apt')
    install_packages = ['pathpilotrobotstarter']

    if not common_path_prefix.exists() or not storage_path.exists():
        return False

    updater = BaseOSUpdater(
        common_path_prefix,
        storage_path,
        repository_path_suffix,
        install_packages,
    )

    updater.copy_new_packages()
    await updater.create_repo()
    await updater.update_base_system()
    updater.delete_repo()
    return True

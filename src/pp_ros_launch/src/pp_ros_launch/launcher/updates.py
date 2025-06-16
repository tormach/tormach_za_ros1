from pp_ros_launch.config import PPROSContainerConfig

from typing import Callable

import datetime

import os

from ..image import pathpilot_versions as pathpilot_versions

from ..image.pathpilot_versions import Version
from ..image.docker_registry import DockerRegistryIOError

from typing import List, Union

import logging

import aiodocker
import asyncio
import re


class UpdaterException(RuntimeError):
    pass


class Updater(PPROSContainerConfig):
    registry_name = os.environ.get('DOCKER_REGISTRY', 'docker.pathpilot.com')

    pathpilot_channels = pathpilot_versions.PathPilotChannels(registry_name)

    logger = logging.getLogger('pp_ros_launch.launcher.Updater')

    @classmethod
    def sort(cls, image_list):
        """Return ``image_list`` in reverse-sorted order so that newest
        versions appear first

        Args:
            image_list (List): Input List

        Returns:
            List: Sorted List
        """
        return list(reversed(sorted(image_list)))

    @classmethod
    async def get_local_channels(
        cls,
    ) -> List[pathpilot_versions.VersionChannelSet]:
        """Return all available local PathPilot Robot Channels

        Returns:
            List[pathpilot_versions.VersionChannel]: List of available channels
        """
        channels = await Updater.pathpilot_channels.get_channels(
            check_nonlocal=False
        )
        return channels

    @classmethod
    async def get_local_channel_names(cls) -> List[str]:
        """Return all available local PathPilot Robot Channels' names

        Returns:
            List[str]: List of available channel names
        """
        channels = await cls.get_local_channels()
        names = [ch.name for ch in channels]
        cls.logger.info(f'Discovered local PathPilot Robot Channels {names}.')
        return names

    @classmethod
    async def get_channel_by_name(
        cls, name: str, check_nonlocal: bool = True
    ) -> Union[pathpilot_versions.VersionChannelSet, None]:
        """Mapping function for PathPilot Robot Channel name to the Python object

        Args:
            name (str): Plainstring name of the channel
            check_nonlocal (bool): Switch if to try to look for remote only channels too

        Returns:
            pathpilot_versions.VersionChannelSet: PathPilot Robot Channel object, None if the channel does not exist
        """
        channels = await Updater.pathpilot_channels.get_channels(check_nonlocal)
        cls.logger.info(f"Searching for a channel by name '{name}'")
        for channel in channels:
            if name == channel.name:
                cls.logger.info(
                    f"Found channel '{channel.name}' when querying for '{name}'"
                )
                return channel
        return None

    @classmethod
    async def get_local_images(
        cls, channel: Union[str, pathpilot_versions.VersionChannelSet]
    ) -> List[pathpilot_versions.LocalVersion]:
        """List local Docker images - PathPilot Robot versions

        Args:
            channel (Union[str, pathpilot_versions.VersionChannelSet]): Channel for which to query

        Returns:
            List[pathpilot_versions.LocalVersion]: List of docker images locally available on the machine
        """
        if isinstance(channel, str):
            channel = await Updater.get_channel_by_name(
                channel, check_nonlocal=False
            )
        if not channel:
            cls.logger.warning(
                f'Specified channel "{channel}" does not exists! '
                'Returning empty list of images!'
            )
            return []

        images = await channel.local_channel.get_all_images()
        cls.logger.info(
            f'Channel {channel.name} includes local images {[image.name for image in images]}'
        )
        return images

    @classmethod
    async def get_all_local_images(
        cls,
    ) -> List[pathpilot_versions.LocalVersion]:
        """List all local Docker images across all channels - PathPilot Robot versions

        Returns:
            List[pathpilot_versions.LocalVersion]: List of docker images locally available on the machine
        """
        channels = await cls.get_local_channels()
        futures = []
        for channel in channels:
            futures.append(cls.get_local_images(channel))
        versions = await asyncio.gather(*futures)
        versions = [item for sublist in versions for item in sublist]
        return versions

    @classmethod
    async def get_default_image(cls) -> pathpilot_versions.LocalVersion:
        """List default Docker image, i.e. last image run

        Returns:
            pathpilot_versions.LocalVersion: Local Docker image, None if no information available
        """
        image_name = cls.get_config("image_name")
        if image_name is None:
            cls.logger.info(
                "No 'image_name' found in config. No default image retrieved!"
            )
            return None
        else:
            channels = await Updater.get_local_channels()
            if channels:
                for channel in channels:
                    images = await Updater.get_local_images(channel)
                    if images:
                        default = [i for i in images if i.name == image_name]
                        if default:
                            default_image = default[0]
                            cls.logger.info(
                                f'Determined default image: {default_image.name}!'
                            )
                            return default_image
            cls.logger.warning(
                f'Staged default image {image_name} is invalid! '
                'No default image retrieved!'
            )
            return None

    @classmethod
    async def get_update(
        cls, channel: Union[str, pathpilot_versions.VersionChannelSet]
    ) -> pathpilot_versions.RemoteVersion:
        """Get available update for a specific channel

        Args:
            channel (Union[str, pathpilot_versions.VersionChannelSet]): Channel for which check the updates

        Returns:
            pathpilot_versions.RemoteVersion: Available remote update, None if no update available
        """
        if isinstance(channel, str):
            channel = await Updater.get_channel_by_name(channel)
        if not channel:
            cls.logger.warning(
                f'Specified channel "{channel}" does not exists! '
                'Returning None update!'
            )
            return None
        try:
            update = await channel.get_update()
        except DockerRegistryIOError:
            cls.logger.error(
                f"Error occured when the remote registry '{channel.remote_channel.registry_prefix}' was queried for update."
            )
            return None

        if update:
            cls.logger.info(
                f'There is update {str(update.version)} {update.codename} '
                f'available for channel "{channel.name}".'
            )
        return update

    @classmethod
    async def get_all_updates(cls) -> List[pathpilot_versions.RemoteVersion]:
        """Wrapper function for querying all available updates across all
        channels

        Returns:
            List[pathpilot_versions.RemoteVersion]: List of update objects
        """
        channels = await Updater.pathpilot_channels.get_channels()
        cls.logger.info(f'Checking updates for channels "{channels}')
        tasks = [
            asyncio.create_task(Updater.get_update(channel))
            for channel in channels
        ]
        updates = [
            update
            for update in await asyncio.gather(*tasks)
            if update is not None
        ]
        if not updates:
            cls.logger.info(f'No updates for channels "{channels}" found!')
        return updates

    @classmethod
    async def delete_local_images(
        cls, images: List[pathpilot_versions.LocalVersion]
    ) -> None:
        """Delete images from Docker daemon and the local storage

        Args:
            images (List[pathpilot_versions.LocalVersion]): Images selected for deletion
        """
        futures = []
        for image in images:
            futures.append(image.delete())

        await asyncio.gather(*futures)

    @classmethod
    async def pull(
        cls, update: pathpilot_versions.RemoteVersion, status_cb=None
    ) -> bool:
        """Pull a specific image tag

        Pull the specified RemoteVersion image.

        Args:
            update (pathpilot_versions.RemoteVersion): Image to pull
            status_cb ([type], optional): Function to call on each change.
                                          two percentage (:py:type:`float`)
                                          arguments:  `overall` for percent complete
                                          of layer downloads, and `current`
                                          for percent complete of current,
                                          ongoing download and extract operations.
                                          The callback will be run periodically
                                          to update the percentages. Defaults to None.

        Returns:
            bool: Success indicator
        """
        try:
            async for overall, current in update.pull():
                if status_cb is not None:
                    status_cb(overall, current)
        except Exception as e:
            cls.logger.error(f"Error occured during pulling {e}")
            return False
        cls.logger.info(
            f"Update {update.name} {str(update.version)} {update.codename} "
            f"succesfully downloaded from {cls.registry_name}!"
        )
        return True

    @classmethod
    async def set_image(cls, image_name: str):
        """Set the Docker image tag to run

        Args:
            image_name (str): Image identification
        """
        channels = await Updater.pathpilot_channels.get_channels(
            check_nonlocal=False
        )
        images = []
        for channel in channels:
            images += await Updater.get_local_images(channel)
        if images:
            image = [i for i in images if i.name == image_name]
            if image:
                image = image[0]
                dra = cls.get_config('docker_run_args', dict())
                # FIXME This is redundant
                dra['image'] = image.name
                cls.set_config('image_name', image.name)
                cls.set_config('image_tag', image.tag)
                # cls.set_config('image_type', image.image_type)
                cls.write_config()
                cls.logger.info(
                    'Successfully set the default image in the Launcher config file '
                    f'to {image.name}'
                )
        cls.logger.warning(
            'Could NOT set the default image in the Launcher config file '
            f"to {image_name}. The image doesn't exist!"
        )

    @classmethod
    def get_set_image(cls):
        image_name = cls.get_config("image_name", None)
        image_tag = cls.get_config("image_tag", None)
        return (image_name, image_tag)

    # One off hackish function which does not rely on asyncio
    # It should be passed away eventually
    @classmethod
    def get_set_image_main_number(cls):
        image_tag = cls.get_config("image_tag", None)
        match = Version.tag_pattern.match(image_tag)
        if match is not None:
            image_number = match.group('image_version_major')
            return image_number
        return None

    @classmethod
    async def check_eula_agreement(cls) -> bool:
        """Check if the user already agreed to the EULA for currently staged version

        Raises:
            RuntimeError: Raised when no default image available

        Returns:
            bool: Indicator if EULA is already agreed for current image
        """
        # DEVEL type of image doesn't need to have EULA, but can have one
        _image_name = cls.get_config('image_name', None)
        if _image_name is None:
            raise RuntimeError(
                'Channot check EULA agreement when image version is not selected'
            )
        _eula_config = cls.get_config('images_with_agreed_eula', dict())
        _eula_item = _eula_config.get(_image_name, None)
        if _eula_item is not None:
            try:
                if (
                    datetime.datetime.fromisoformat(_eula_item.get('date'))
                    < datetime.datetime.now()
                ):
                    cls.logger.info(
                        f'EULA agreement record for image {_image_name} found!'
                    )
                    return True
            except ValueError:
                _eula_config.pop(_image_name)
                cls.set_config('images_with_agreed_eula', _eula_config)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, cls.write_config)
                cls.logger.info(
                    f'EULA agreement record for image {_image_name} was incorrect and was deleted'
                )
        cls.logger.info(
            f'No EULA greement record for image {_image_name} found!'
        )
        return False

    @classmethod
    async def agree_with_eula(cls) -> None:
        """Store tha the user agreed with EULA on the currently staged image

        Raises:
            RuntimeError: Raised when no staged to run version
        """
        _eula_config = cls.get_config('images_with_agreed_eula', dict())
        _image_name = cls.get_config('image_name', None)
        if _image_name is None:
            raise RuntimeError(
                'Image_name config is empty during agreeing to EULA!'
            )
        _version_data = {'date': datetime.datetime.now().isoformat()}
        _eula_config[_image_name] = _version_data
        cls.set_config('images_with_agreed_eula', _eula_config)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls.write_config)
        cls.logger.info(f'EULA agreement for image {_image_name} was recorded')

    @classmethod
    async def _load(cls, path: str):
        """Load image from path

        Generator passing two values (int, int) is returned
        to monitor progress.

        This method is in this class simply because it uses the
        docker python API.

        Args:
            path (str): Path to the image to load

        Raises:
            RuntimeError: Raised when the path is not valid
            RuntimeError: Raised on unknow Docker error
            RuntimeError: Raised when error occurs during loading of the image

        Yields:
            [(layers, percentage, images)]: Yields the current status of loading
        """
        try:
            async with aiodocker.docker.Docker() as docker:
                di = aiodocker.images.DockerImages(docker)
                with open(path, 'rb') as f:
                    async_gen = di.import_image(f, stream=True, quiet=False)

                    layers = []
                    image_regex_string = 'Loaded image(?: ID)?: ([^\\s]+)\\n'
                    image_regex = re.compile(image_regex_string)
                    async for line in async_gen:
                        percentage = None
                        images = None
                        if 'id' in line and line['id'] != '':
                            _id = line.get('id')
                            layers.append(_id) if _id not in layers else layers
                        if 'status' in line and line['status'].startswith(
                            'Loading layer'
                        ):
                            current = line.get('progressDetail', dict()).get(
                                'current', 0
                            )
                            total = line.get('progressDetail', dict()).get(
                                'total', 0
                            )
                            percentage = (
                                int(100 * current / total) if total != 0 else 0
                            )
                        if 'stream' in line and line.get(
                            'stream', ''
                        ).startswith('Loaded image'):
                            image_matches = image_regex.finditer(line['stream'])
                            for group in image_matches:
                                if not images:
                                    images = []
                                i = group.group(1)
                                images.append(i)
                        if ('errorDetail' or 'error') in line:
                            error: str = line.get('errorDetail', dict()).get(
                                'message', 'Error not specified!'
                            )
                            raise RuntimeError(error)

                        yield (
                            len(layers) if percentage is not None else None,
                            percentage,
                            images,
                        )
        except (PermissionError, FileNotFoundError):
            raise RuntimeError(f"Specified path {path} is not valid!")
        except Exception as e:
            raise RuntimeError(f"Docker API error. {e}")

    @classmethod
    async def load(
        cls, path: str, status_cb: Callable[[int, int], None] = None
    ) -> dict:
        """Load image (or images) from specified path

        Load docker image.  Returns a local
        image object.

        Pass an optional ``status_cb`` with two (:py:type:`int`)
        arguments:  `layer` for the current layer on which
        system operates, and `percentage` for percent complete of
        current layer loading.  The callback will be run periodically
        to update the percentages.
        """
        valid_images: list = []
        error_images: list = []

        try:
            gen = Updater._load(path)
            async for layer, percentage, images in gen:
                Updater.logger.info(
                    f'Loading from {path} status update: '
                    f'layer: {layer}, percentage: {percentage}. '
                    f'Images finished: {images if images else "no images"}'
                )
                if (status_cb is not None) and (
                    layer and percentage
                ) is not None:
                    status_cb(layer, percentage)
                if images is not None:
                    for i in images:
                        if Version.tag_pattern.search(i):
                            valid_images.append(i)
                        else:
                            async with aiodocker.docker.Docker() as docker:
                                await aiodocker.images.DockerImages(
                                    docker
                                ).delete(i)
                            error_images.append(i)
        except Exception as e:
            _raise_error: bool = False
            async with aiodocker.docker.Docker() as docker:
                di = aiodocker.images.DockerImages(docker)
                for i in valid_images:
                    try:
                        await di.delete(i)
                    except Exception:
                        _raise_error = True
                for i in error_images:
                    try:
                        await di.delete(i)
                    except Exception:
                        _raise_error = True
                if _raise_error:
                    raise UpdaterException(
                        "Error occured furing deleting of images in exception handling",
                        *e.args,
                    )
            raise UpdaterException(*e.args)
        return {
            'valid_images': valid_images,
            'error_images': error_images,
        }

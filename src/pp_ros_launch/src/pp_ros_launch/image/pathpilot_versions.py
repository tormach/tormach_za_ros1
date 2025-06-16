import semver
import datetime
import aiodocker
import asyncio
import re
import dateutil.parser
import base64

from pp_ros_launch.image import docker_registry, registry_information
import pp_account

from typing import Dict, List, Optional, AsyncIterator, Union


class _Singleton(type):
    # Should really be a loop-local storage
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]


class DockerClientProvider(metaclass=_Singleton):
    """ """

    def __init__(self):
        self._docker = aiodocker.Docker()

    async def _close(self) -> None:
        await self._docker.close()

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._close())
            else:
                loop.run_until_complete(self._close())
        except Exception:
            pass

    @property
    def docker(self) -> aiodocker.docker.Docker:
        return self._docker


class Version:
    """
    Base class for a single release version (Docker image)
    """

    tag_pattern_string = r'(?:[^-]+)-dist-(?:[^-]+)-(?P<image_version_major>[0-9]+)\.(?P<image_version_minor>[0-9a-f]+)'
    tag_pattern = re.compile(tag_pattern_string)

    def __init__(
        self,
        registry_information: registry_information.RegistryInformation,
        channel_name: str,
        tag: str,
        labels: Dict[str, str],
        build_time: Optional[datetime.datetime] = None,
        image_version_major: Optional[str] = None,
        image_version_minor: Optional[str] = None,
    ):
        self._registry_information = registry_information
        self._channel_name = channel_name
        self._tag = tag
        self._labels = labels
        self._build_time = build_time
        if (image_version_major or image_version_minor) is None:
            tag_match = Version.tag_pattern.match(tag)
            if tag_match is None:
                raise ValueError(
                    f'Tag {tag} does not have the right format: {Version.tag_pattern_string}'
                )
            self._image_version_major = int(
                tag_match.group('image_version_major')
            )
            self._image_version_minor = tag_match.group('image_version_minor')
        else:
            self._image_version_major = int(image_version_major)
            self._image_version_minor = image_version_minor
            if (image_version_major or image_version_minor) not in tag:
                raise ValueError(
                    "Passed image version numbers are not valid for given tag"
                )

    @property
    def image_version(self) -> str:
        return f"{self._image_version_major}.{self._image_version_minor}"

    @property
    def image_version_major(self) -> int:
        return self._image_version_major

    @property
    def version(self) -> semver.VersionInfo:
        version: str = self.get_label('com.tormach.pathpilot.robot.version')
        # Remove after apropriate amount of time
        # RELEASE_VERSION label no longer used and replaced with com.tormach.pathpilot.robot.version
        version = (
            self.get_label('RELEASE_VERSION')
            if version is None or ''
            else version
        )
        try:
            return semver.VersionInfo.parse(version)
        except (TypeError, ValueError):
            return semver.VersionInfo.parse('0.0.0')

    @property
    def codename(self) -> str:
        return self.get_label('com.tormach.pathpilot.robot.codename')

    @property
    def description(self) -> str:
        return self.get_label('com.tormach.pathpilot.robot.description')

    @property
    def changelog(self) -> str:
        return self.get_label('com.tormach.pathpilot.robot.changelog')

    @property
    def eula(self) -> str:
        return self.get_label('com.tormach.pathpilot.robot.eula')

    @property
    def git_revision(self) -> str:
        return self.get_label('com.tormach.pathpilot.robot.git.rev')

    @property
    def build_time(self) -> Optional[datetime.datetime]:
        return self._build_time

    @property
    def publish_time(self) -> datetime.datetime:
        creation_time = self.get_label('com.tormach.pathpilot.robot.createdAt')
        try:
            return datetime.datetime.fromisoformat(creation_time)
        except (ValueError, TypeError):
            return (
                self.build_time
                if self.build_time is not None
                else datetime.datetime.now()
            )

    @property
    def image_labels(self) -> Dict[str, str]:
        return dict(self._labels)

    @property
    def registry_prefix(self) -> str:
        return self._registry_information.prefix

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @property
    def name(self) -> str:
        return f"{self._registry_information.prefix}{'/' if self._registry_information.prefix != '' else ''}{self._channel_name}:{self._tag}"

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def _sort_key(self):
        return self.version

    def get_label(self, label: str) -> Optional[str]:
        return self._labels.get(label, None)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self):
        return (
            f'{type(self).__name__}(registry_information={self._registry_information}, '
            f'channel_name={self._channel_name}, tag={self._tag}, labels={self._labels}, '
            f'build_time={self._build_time}, image_version_major={self._image_version_major}, '
            f'image_version_minor={self._image_version_minor})'
        )

    def _cmp(self, other):
        return self._sort_key.compare(other._sort_key)

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    # For EQUAL and not EQUAL comparison, the name of the OCI image has to be taken
    # under consideration, as there may be multiple versions with the same 'semver'
    # version number which causes problems with unique identification

    def __eq__(self, other):
        return self._cmp(other) == 0 and self.name == other.name

    def __ne__(self, other):
        return self._cmp(other) != 0 or self.name != other.name


class LocalVersion(Version):
    """ """

    async def delete(self, force=True) -> list:
        async with aiodocker.docker.Docker() as docker:
            return await docker.images.delete(self.name, force=force)


class RemoteVersion(Version):
    """ """

    @property
    def registry_domain(self) -> str:
        return self._registry_information.domain

    async def pull(self) -> AsyncIterator:
        default_account = (
            await pp_account.ContainerRegistryAccount.default_account(
                self.registry_domain
            )
        )
        login_string = f'{await default_account.username()}:{await default_account.password()}'
        login = login_string.encode('utf-8')
        login_base64 = base64.b64encode(login)
        auth = {'auth': login_base64}

        layers = {}

        async with aiodocker.docker.Docker() as docker:
            async for item in docker.images.pull(
                self.name, stream=True, auth=auth
            ):
                if 'id' not in item:
                    continue
                _id = item['id']
                layer = layers.setdefault(_id, dict(id=_id, complete=False))
                s = item['status']

                # Update layer status
                if s == 'Already exists':
                    layer['complete'] = True
                elif s == 'Downloading' or s == 'Extracting':
                    pd = item['progressDetail']
                    if 'total' in pd:
                        # Sometimes progressDetail has 'current' but no 'total'
                        t = layer['total'] = pd['total']
                        alpha = t * 0.5 if s == 'Extracting' else 0
                        layer['current'] = alpha + pd['current'] * 0.5
                elif s == 'Pull complete':
                    layer['complete'] = True
                elif s.startswith('Pulling from'):
                    layers.pop(_id)
                    continue

                # Calculate progress
                layers_complete = [
                    layer for layer in layers.values() if layer['complete']
                ]
                layers_incomplete = [
                    layer for layer in layers.values() if not layer['complete']
                ]
                layers_in_progress = [
                    layer for layer in layers_incomplete if 'current' in layer
                ]
                # - Percent complete of overall layer download
                if len(layers) > 0:
                    progress_overall = int(
                        100.0 * len(layers_complete) / len(layers)
                    )
                else:  # Avoid ZeroDivisionError
                    progress_overall = 0
                # - Percent complete of currently ongoing operations
                current = sum(layer['current'] for layer in layers_in_progress)
                total = sum(layer['total'] for layer in layers_in_progress)
                if total > 0:
                    progress_current = int(100.0 * current / total)
                else:  # Avoid ZeroDivisionError
                    progress_current = 0

                # Yield progress
                yield (progress_overall, progress_current)


class VersionChannel:
    """
    Base class for PathPilot Robot Version channel

    Used as a set of updates to one product state and should not include unconsistent
    release lines
    """

    def __init__(
        self,
        name: str,
        registry_information: registry_information.RegistryInformation,
    ):
        self._name = name
        self._registry_information = registry_information

    @property
    def name(self) -> str:
        return self._name

    @property
    def registry_prefix(self) -> str:
        return self._registry_information.prefix

    def get_all_images(self):
        """
        Returns all possible versions in the set
        """
        return []

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f'{type(self).__name__}(name={self._name}, '
            f'registry_information={self._registry_information})'
        )


class LocalVersionChannel(VersionChannel):
    def __init__(
        self,
        name: str,
        registry_information: registry_information.RegistryInformation,
    ):
        super().__init__(name, registry_information)
        self._repo_tags_pattern = re.compile(
            rf'^{self.registry_prefix}/?{self.name}:(?P<image_tag>{Version.tag_pattern_string})$'
        )

    async def get_all_images(self, newer_then: Union[str, int] = None):
        list_of_images = []
        async with aiodocker.docker.Docker() as docker:
            for image in await docker.images.list():
                repo_tags = image.get('RepoTags', [])
                for tag in repo_tags if repo_tags else []:
                    match = self._repo_tags_pattern.search(tag)
                    if match is not None:
                        list_of_images.append(
                            LocalVersion(
                                self._registry_information,
                                self.name,
                                match.group('image_tag'),
                                image.get('Labels', []),
                                datetime.datetime.fromtimestamp(
                                    image.get('Created', 0)
                                ),
                                match.group('image_version_major'),
                                match.group('image_version_minor'),
                            )
                        )
                        continue
            return list_of_images


class RemoteVersionChannel(VersionChannel):
    def __init__(
        self,
        name: str,
        registry_information: registry_information.RegistryInformation,
    ):
        super().__init__(name, registry_information)
        self._repo_tags_pattern = re.compile(
            rf'(?P<image_tag>{Version.tag_pattern_string})$'
        )
        self._remote_repository = docker_registry.docker_repository_factory(
            self.name, self._registry_information
        )

    async def _extract_labels(self, reference):
        image = await self._remote_repository.get_manifests_by_reference(
            reference
        )

        config_digest = image.get('config', dict()).get('digest', None)
        if config_digest is None:
            return []

        config_blob = await self._remote_repository.get_blob_by_digest(
            config_digest
        )

        labels = config_blob.get('config', dict()).get('Labels', dict())

        return labels

    async def _get_created_date(self, reference):
        image = await self._remote_repository.get_manifests_by_reference(
            reference
        )

        config_digest = image.get('config', dict()).get('digest', None)
        if config_digest is None:
            return None  # datetime.datetime.fromtimestamp(0)

        config_blob = await self._remote_repository.get_blob_by_digest(
            config_digest
        )

        try:
            created_iso = config_blob.get('created', None)
            created = dateutil.parser.parse(created_iso)
        except Exception:
            created = None

        return created

    async def get_all_images(
        self, newer_then: Optional[Union[str, int]] = None
    ) -> List[RemoteVersion]:
        if newer_then is not None:
            try:
                if isinstance(newer_then, str):
                    newer_then = int(newer_then)
                if not isinstance(newer_then, int):
                    raise Exception()
            except Exception:
                newer_then = None
        try:
            all_tags = await self._remote_repository.get_tags_list()
        except docker_registry.DockerRegistryInvalidRequest:
            return []

        list_of_images = []

        futures = []

        async def _create(tag: str):
            match = self._repo_tags_pattern.search(tag)
            if (match is None) or (
                newer_then is not None
                and newer_then > int(match.group('image_version_major'))
            ):
                return
            labels = await self._extract_labels(tag)
            created = await self._get_created_date(tag)
            image_version_major = match.group('image_version_major')
            image_version_minor = match.group('image_version_minor')
            list_of_images.append(
                RemoteVersion(
                    self._registry_information,
                    self.name,
                    tag,
                    labels,
                    created,
                    image_version_major,
                    image_version_minor,
                )
            )

        for tag in all_tags:
            futures.append(asyncio.ensure_future(_create(tag)))

        await asyncio.gather(*futures)
        return list_of_images


class VersionChannelSet:
    def __init__(
        self,
        channel_name: str,
        registry_information: registry_information.RegistryInformation,
    ):
        self._channel_name = channel_name
        self._local_channel = LocalVersionChannel(
            self.name, registry_information
        )
        self._remote_channel = RemoteVersionChannel(
            self.name, registry_information
        )

    @property
    def name(self) -> str:
        return self._channel_name

    @property
    def local_channel(self) -> LocalVersionChannel:
        return self._local_channel

    @property
    def remote_channel(self) -> RemoteVersionChannel:
        return self._remote_channel

    async def get_update(self) -> Optional[RemoteVersion]:
        """
        The update process is dependent on always increasing major image number.

        (Each new release has to have a higher major number than any of the previous ones.)
        """
        local_images = await self.local_channel.get_all_images()

        update: Optional[Version] = None

        if local_images:
            sorted_images = sorted(local_images)
            latest_local_major_image_version = sorted_images[
                -1
            ].image_version_major
        else:
            latest_local_major_image_version = None

        possible_updates = await self.remote_channel.get_all_images(
            newer_then=latest_local_major_image_version
        )

        if possible_updates:
            # In case there is multiple images with the same PathPilot version, try to get
            # the image with highest major image version (as this should be ever increasing).
            # In the case there are still multiple images, get the one with latest build time

            sorted_possible_updates = sorted(possible_updates)
            highest_version = sorted_possible_updates[-1].version
            highest_version_updates = [
                i
                for i in sorted_possible_updates
                if i.version == highest_version
            ]

            if len(highest_version_updates) > 1:
                sorted_highest_version_updates = sorted(
                    highest_version_updates, key=lambda x: x.image_version_major
                )
                highest_image_version = sorted_highest_version_updates[
                    -1
                ].image_version_major
                highest_image_version_updates = [
                    i
                    for i in sorted_possible_updates
                    if i.image_version_major == highest_image_version
                ]

                if len(highest_image_version_updates) > 1:
                    sorted_highest_image_version_updates = sorted(
                        highest_version_updates, key=lambda x: x.build_time
                    )
                    update = sorted_highest_image_version_updates[-1]
                else:
                    update = highest_image_version_updates[0]

            else:
                update = highest_version_updates[0]

        if update and update in local_images:
            update = None

        return update

    async def update(self) -> AsyncIterator:
        update = await self.get_update()
        if update:
            return update.pull()
        raise StopAsyncIteration

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f'{type(self).__name__}(channel_name={self._channel_name}, '
            f'registry_information={self._local_channel._registry_information})'
        )


class PathPilotChannels:
    """ """

    def __init__(self, registry_prefix: str):
        self._channels = None
        self._registry_information = (
            registry_information.get_registry_information_from_prefix(
                registry_prefix
            )
        )
        self._remote_registry = docker_registry.docker_registry_factory(
            self._registry_information
        )
        # Special case for the Docker HUB inconsistency
        prefix = (
            rf'{self.registry_information.prefix}\/'
            if self.registry_information.prefix != ''
            else r'(?![\w\.]+\.[a-z]{2,63}\/)'
        )
        self._channel_names_pattern = re.compile(
            rf'^{prefix}(?P<channel_name>[\w\.\-\_\~\/]+):(?:{Version.tag_pattern_string})$'
        )

    async def get_channels_cache(self) -> Optional[List]:
        """
        Cache channels to avoid unnecessary penalty when querying for new list

        There is presumption that new channels will not be added that often
        """

        if self._channels is None:
            await self.get_channels()
        return self._channels

    @property
    def registry_information(self) -> registry_information.RegistryInformation:
        return self._registry_information

    async def get_channels(
        self, check_nonlocal=True
    ) -> List[VersionChannelSet]:
        """
        There are Local and Remote channels actually

        To list the Local channels, program needs to loop over all images and separate ones
        with the tags in the right format, inspect the repositories specified and create
        a list from that.

        To list the Remote channels, program needs to ask the Registry which repositories
        the user has access to.
        """

        # How to differentiate between docker.io images and images prefixed with the registry

        local_channels = []
        async with aiodocker.docker.Docker() as docker:
            for image in await docker.images.list():
                repo_tags = image.get('RepoTags', [])
                for image in repo_tags if repo_tags else []:
                    match = self._channel_names_pattern.search(image)
                    if match is None:
                        continue
                    local_channels.append(match.group('channel_name'))

        remote_channels = []
        if check_nonlocal:

            async def _check_images(
                repository: docker_registry.DockerRepository,
            ):
                try:
                    tags = await repository.get_tags_list()
                except Exception:
                    return
                for tag in tags:
                    match = Version.tag_pattern.search(tag)
                    if match is not None:
                        remote_channels.append(repository.name)
                        return

            futures = []

            all_repositories = (
                await self._remote_registry.get_all_repositories()
            )

            for repository in all_repositories:
                futures.append(asyncio.ensure_future(_check_images(repository)))

            await asyncio.gather(*futures)

        channel_sets = []

        for channel in list(set(local_channels + remote_channels)):
            channel_sets.append(
                VersionChannelSet(channel, self.registry_information)
            )

        return channel_sets

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{type(self).__name__}(registry_prefix={self._registry_information.prefix})'

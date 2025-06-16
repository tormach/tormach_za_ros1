#
# pp_ros_releases.py
#
# Manage ROS releases from a Docker registry
#
# Uses semantic versioning to compare images; see
# https://semver.org/ - with few tweaks, see software_version()
# definition

import os
import re
import copy
import docker
import semver
import datetime
import dateutil.parser
from pp_ros_launch.image.docker_hub import DockerRepo, DockerRegistryIOError
from pp_ros_launch.config import PPROSContainerConfig
from dataclasses import dataclass
from typing import Union


@dataclass
class LauncherVersionModel:
    tag: str
    version: str
    codename: str
    description: str
    git_sha: str
    created_at: datetime.datetime
    changelog: str
    eula: str

    def __str__(self) -> str:
        return f"TAG: {self.tag}, Version: {self.version}, Codename: {self.codename}, Description: {self.description}, Creation date: {self.created_at}"


class PPRosImageVersionException(RuntimeError):
    pass


class PPRosImageVersion(PPROSContainerConfig):
    ROS_DISTRO = os.environ.get('ROS_DISTRO', 'kinetic')
    DEBIAN_SUITE = os.environ.get('DEBIAN_SUITE', 'stretch')
    IMAGE_VERSION = os.environ.get('IMAGE_VERSION', None)
    IMAGE_TYPE = os.environ.get('IMAGE_TYPE', 'dist')
    DOCKER_REPOSITORY = os.environ.get('DOCKER_REPO')
    DOCKER_REGISTRY = os.environ.get('DOCKER_REGISTRY')
    DOCKER_REPO = f'{DOCKER_REGISTRY}/{DOCKER_REPOSITORY}'
    image_types = {'dist', 'devel'}
    image_location = None  # Subclasses override

    @property
    def docker_repo(self):
        return self.DOCKER_REPO

    def __init__(self, image_tag):
        super().__init__()
        image_tag = str(image_tag)  # Remove unicode
        self.image_tag = image_tag
        (
            self.ros_distro,
            self.image_type,
            self.debian_suite,
            self.image_version_major,
            self.image_version_hash,
        ) = self.parse_image_tag(image_tag)
        self.image_version_major = int(self.image_version_major)

    # Parse image versions, `109+09eab32f` or old `109.09eab32f`
    image_version_re_str = r'^([0-9]+)[.+]([0-9a-f]+)$'
    image_version_re = re.compile(image_version_re_str)
    # Parse image tags
    image_tag_re_str = r'^([^-]+)-(dist|devel)-([^-]+)-([0-9]+)\.([0-9a-f]+)$'
    image_tag_re = re.compile(image_tag_re_str)

    @classmethod
    def parse_image_tag(cls, image_tag):
        m = cls.image_tag_re.match(image_tag)
        if not m:
            raise RuntimeError("Unable to parse image tag '%s'" % image_tag)
        elts = list(m.groups())
        elts[3] = int(elts[3])
        return elts

    @classmethod
    def construct_image_tag(cls, *args):
        if len(args) != 5:
            raise RuntimeError("construct_image_tag() requires 5 args")
        if args[1] not in cls.image_types:
            raise RuntimeError(
                "arg 2 must be in ('%s'); '%s' invalid"
                % ("'|'".join(cls.image_types), args[1])
            )
        return "%s-%s-%s-%s.%s" % args

    @classmethod
    def is_valid_image_tag(cls, image_tag):
        return cls.image_tag_re.match(image_tag) is not None

    @classmethod
    def all_images(cls):
        raise NotImplementedError("Subclasses must implement all_images()")

    @classmethod
    def image_by_version(cls, image_version, image_type):
        version_match = cls.image_version_re.match(image_version)
        if version_match is None:
            raise RuntimeError("image_version must be format <major>+<hash>")
        image_version = '+'.join(version_match.groups())

        all_images = cls.all_images()
        for i in all_images:
            if i.image_version == image_version and i.image_type == image_type:
                return i
        return None

    @classmethod
    def image_by_tag(cls, image_tag):
        all_images = cls.all_images()
        for i in all_images:
            if i.image_tag == image_tag:
                return i
        return None

    _invalid_version = semver.VersionInfo.parse('0.0.0')

    @property
    def launcher_image_model(self) -> LauncherVersionModel:
        _version = self.software_version
        return LauncherVersionModel(
            tag=self.image_tag,
            # Software version in SemVer format do NOT need to be localized
            version=(
                str(_version) if _version != self._invalid_version else None
            ),
            codename=self.codename,
            created_at=self.created_at,
            description=self.description,
            git_sha=self.git_rev,
            changelog=self.changelog,
            eula=self.eula,
        )

    @classmethod
    def this_image(cls):
        if cls.IMAGE_VERSION is None:
            raise RuntimeError("IMAGE_VERSION not set in environment")
        image_version = cls.image_version_re.match(cls.IMAGE_VERSION)
        if image_version is None:
            raise RuntimeError("IMAGE_VERSION must be format <major>+<hash>")
        image_version_major, image_version_hash = image_version.groups()
        image_tag = cls.construct_image_tag(
            cls.ROS_DISTRO,
            cls.IMAGE_TYPE,
            cls.DEBIAN_SUITE,
            image_version_major,
            image_version_hash,
        )
        return cls(image_tag)

    @property
    def image_version(self):
        return f"{self.image_version_major}+{self.image_version_hash}"

    def image_labels(self):
        raise NotImplementedError("Subclasses must implement image_labels()")

    def label(self, label_name):
        labels = self.image_labels()
        return labels.get(label_name, None)

    @property
    def software_version(self) -> semver.VersionInfo:
        _version: str = self.label('com.tormach.pathpilot.robot.version')
        # Remove after apropriate amount of time
        # RELEASE_VERSION label no longer used and replaced with com.tormach.pathpilot.robot.version
        _version = (
            self.label('RELEASE_VERSION')
            if _version is None or ''
            else _version
        )
        try:
            # Remove after apropriate amount of time
            # NEVER USED SINCE PUBLIC BETA RELEASE
            # Retroactively convert '-pre.99.07924946' to '-pre.99+07924946'
            # ('0.1.0-pre.99.07924946' is invalid b/c of leading '0')
            # However, because of the meaning where the 99 represents major
            # version number of PathPilot Robot container image and 07924946
            # represents a git hash (shortened) of the last change, we also want
            # to replace 108.c20c541a to 108+c20c541a and nothing else
            # For comparison, the major number only is significant
            # Is this still needed?
            _r = re.compile(
                r'^(\d\.\d\.\d-pre\.\d{1,4})(?:\.)([0-9a-z]{1,}.{1,})$'
            )
            if _r.match(_version):
                _version = _r.sub(r'\1+\2', _version)

            return semver.VersionInfo.parse(_version)
        except (TypeError, ValueError):
            return copy.copy(self._invalid_version)

    @property
    def codename(self) -> str:
        _codename = self.label('com.tormach.pathpilot.robot.codename')
        if _codename == '':
            _codename = None
        return _codename

    @property
    def description(self) -> str:
        _description = self.label('com.tormach.pathpilot.robot.description')
        if _description == '':
            _description = None
        return _description

    @property
    def changelog(self) -> str:
        _changelog = self.label('com.tormach.pathpilot.robot.changelog')
        if _changelog == '':
            _changelog = None
        return _changelog

    @property
    def eula(self) -> str:
        _eula = self.label('com.tormach.pathpilot.robot.eula')
        if _eula == '':
            _eula = None
        return _eula

    @property
    def created_at(self) -> datetime.datetime:
        _created_at = self.label('com.tormach.pathpilot.robot.createdAt')
        try:
            return datetime.datetime.fromisoformat(_created_at)
        except (ValueError, TypeError):
            return (
                self.build_time
                if self.build_time is not None
                else datetime.datetime.now()
            )

    @property
    def git_rev(self) -> str:
        _git_rev = self.label('com.tormach.pathpilot.robot.git.rev')
        if _git_rev == '':
            _git_rev = None
        return _git_rev

    @property
    def build_time(self) -> datetime.datetime:
        raise NotImplementedError("Subclasses must implement build_time()")

    @classmethod
    def tag_part_of_image_name(cls, image_name: str) -> str:
        try:
            if image_name.startswith(cls.DOCKER_REPO):
                tag = image_name.replace(cls.DOCKER_REPO + ':', '', 1)
                if cls.is_valid_image_tag(tag):
                    return tag
        except TypeError:
            pass
        return None

    @property
    def image_name(self):
        """The full name of the image, in ``repo:tag`` format"""
        return f'{self.docker_repo}:{self.image_tag}'

    @classmethod
    def is_valid_image_name(cls, image_name: str) -> bool:
        tag = cls.tag_part_of_image_name(image_name)
        if tag is not None:
            return True
        return False

    def __str__(self):
        return '<PathPilot %s %s Image v. %d+%s>' % (
            self.image_type,
            self.image_location,
            self.image_version_major,
            self.image_version_hash,
        )

    def __repr__(self):
        return self.__str__()

    @property
    def sort_key(self):
        return self.software_version

    def _cmp(self, other):
        return self.sort_key.compare(other.sort_key)

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __eq__(self, other):
        return self._cmp(other) == 0

    def __ne__(self, other):
        return self._cmp(other) != 0


class PPRosHubImageVersion(PPRosImageVersion):
    image_location = "Hub"
    _docker_repo = DockerRepo(PPRosImageVersion.DOCKER_REPO)

    @classmethod
    def all_images(cls):
        try:
            versions = [
                cls(image_tag=t)
                for t in cls._docker_repo.get_tags_list()
                if cls.is_valid_image_tag(t)
            ]
        except DockerRegistryIOError as e:
            raise PPRosImageVersionException(*e.args)
        return versions

    def image_manifest(self):
        try:
            return self._docker_repo.get_manifests_by_reference(self.image_tag)
        except DockerRegistryIOError as e:
            raise PPRosImageVersionException(*e.args)

    def image_labels(self):
        # Attempt to return cached labels
        cache = self.get_config('image_label_cache', dict())
        cache_image_item = cache.get(self.image_name, None)
        if cache_image_item is not None:
            try:
                last_download_date = cache_image_item.get('date', None)
                if last_download_date is not None:
                    if datetime.datetime.fromisoformat(last_download_date) > (
                        datetime.datetime.now() - datetime.timedelta(days=60)
                    ):
                        return cache_image_item.get('labels', dict())
            except ValueError:
                pass

        # Otherwise retrieve labels, cache them & return
        try:
            labels = self._docker_repo.get_labels(self.image_tag)
        except DockerRegistryIOError as e:
            raise PPRosImageVersionException(*e.args)
        if labels is None:
            labels = dict()
        cache_image_item = {
            'date': datetime.datetime.now().isoformat(),
            'labels': labels,
        }
        cache[self.image_name] = cache_image_item
        self.set_config('image_label_cache', cache)
        return labels

    def pull(self):
        yield from PPRosLocalImageVersion.pull(self.image_tag)


class PPRosLocalImageVersion(PPRosImageVersion):
    image_location = "Local"

    @classmethod
    def docker_client(cls):
        if not hasattr(cls, "_docker_client"):
            cls._docker_client = docker.from_env()
        return cls._docker_client

    @classmethod
    def docker_client_raw(cls):
        return cls.docker_client().api

    def __init__(self, image_tag, *args):
        super().__init__(image_tag, *args)

    @classmethod
    def pull(cls, image_tag):
        """Pull an image tag

        This method pulls the given image tag.  To indicate progress,
        it is implemented as a generator returning two percentages:
        an overall percentage of layers downloaded, and a current
        percentage of download/extract operations in progress.

        This method is in this class simply because it uses the
        docker python API.
        """
        try:
            g = cls.docker_client_raw().pull(
                cls.DOCKER_REPO, tag=image_tag, stream=True, decode=True
            )
        except docker.errors.NotFound:
            raise PPRosImageVersionException(
                f'No such remote image "{cls.DOCKER_REPO}/{image_tag}"'
            )
        except docker.errors.APIError as e:
            raise PPRosImageVersionException(*e.args)

        layers = dict()
        for i in g:
            if 'id' not in i:
                continue
            id = i['id']
            layer = layers.setdefault(id, dict(id=id, complete=False))
            s = i['status']

            # Update layer status
            if s == 'Already exists':
                layer['complete'] = True
            elif s == 'Downloading' or s == 'Extracting':
                pd = i['progressDetail']
                if 'total' in pd:
                    # Sometimes progressDetail has 'current' but no 'total'
                    t = layer['total'] = pd['total']
                    alpha = t * 0.5 if s == 'Extracting' else 0
                    layer['current'] = alpha + pd['current'] * 0.5
            elif s == 'Pull complete':
                layer['complete'] = True
            elif s.startswith('Pulling from'):
                layers.pop(id)
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

    @classmethod
    def load(cls, path: str):
        """Load image from path

        Generator passing two values (int, int) is returned
        to monitor progress.

        This method is in this class simply because it uses the
        docker python API.
        """
        try:
            with open(path, 'rb') as f:
                gen = cls.docker_client_raw().load_image(f, quiet=False)
        except (PermissionError, FileNotFoundError):
            raise PPRosImageVersionException(
                f"Specified path {path} is not valid!"
            )
        except docker.errors.APIError:
            raise PPRosImageVersionException("Docker API error.")
        layers = []
        image_regex_string = 'Loaded image(?: ID)?: ([^\\s]+)\\n'
        image_regex = re.compile(image_regex_string)
        for line in gen:
            percentage = None
            images = None
            if 'id' in line and line['id'] != '':
                _id = line.get('id')
                layers.append(_id) if _id not in layers else layers
            if 'status' in line and line['status'].startswith('Loading layer'):
                current = line.get('progressDetail', dict()).get('current', 0)
                total = line.get('progressDetail', dict()).get('total', 0)
                percentage = int(100 * current / total) if total != 0 else 0
            if 'stream' in line and line.get('stream', '').startswith(
                'Loaded image'
            ):
                image_matches = image_regex.finditer(line['stream'])
                for group in image_matches:
                    if not images:
                        images = []
                    i = group.group(1)
                    if cls.is_valid_image_name(i):
                        i = cls(cls.tag_part_of_image_name(i))
                    images.append(i)
            if ('errorDetail' or 'error') in line:
                error: str = line.get('errorDetail', dict()).get(
                    'message', 'Error not specified!'
                )
                raise PPRosImageVersionException(error)
            yield (
                len(layers) if percentage is not None else None,
                percentage,
                images,
            )

    @classmethod
    def delete(cls, image: Union[object, str]) -> None:
        name = (
            image.image_name
            if isinstance(image, PPRosLocalImageVersion)
            else image
        )
        try:
            cls.docker_client_raw().remove_image(name)
        except docker.errors.ImageNotFound:
            if isinstance(image, PPRosLocalImageVersion):
                raise PPRosImageVersionException(f"Cannot delete image {name}")
            # Fail silently

    @property
    def image_data(self):
        if not hasattr(self, '_image_data'):
            self._image_data = self.docker_client().images.get(
                f'{self.DOCKER_REPO}:{self.image_tag}'
            )
        if not hasattr(self, '_image_data'):
            raise KeyError("No such image")
        return self._image_data

    @property
    def build_time(self) -> datetime.datetime:
        _build_time = self.image_data.attrs.get('Created')
        try:
            return dateutil.parser.parse(_build_time)
        except (ValueError, TypeError):
            return None  # If this happens, something is ***seriously*** wrong with this image

    @classmethod
    def all_images(cls):
        all_tags = []
        image_list = cls.docker_client().images.list()
        for image in image_list:
            all_tags += image.tags
        all_tags = [
            (t.split(':') + [''])[1]
            for t in all_tags
            if t.startswith('%s:' % cls.DOCKER_REPO)
        ]
        versions = [
            cls(image_tag=t) for t in all_tags if cls.is_valid_image_tag(t)
        ]
        return versions

    def image_labels(self):
        return self.image_data.labels


if __name__ == "__main__":
    print("Local images:")
    for img in PPRosLocalImageVersion.all_images():
        print(f'{img.docker_repo}:{img.image_tag}')
    print("Hub images:")
    for img in PPRosHubImageVersion.all_images():
        print(f'{img.docker_repo}:{img.image_tag}')

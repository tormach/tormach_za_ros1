#
# Python Docker API
# https://docker-py.readthedocs.io/en/stable/index.html

import os
from .subsystem import SubSystemCheck, SubSystem
from pp_ros_launch.image.versions import PPRosLocalImageVersion
from pp_ros_launch.image.registry_information import (
    InvalidRegistryInformationError,
)
import pp_ros_launch.image.pathpilot_versions as pathpilot_versions
import asyncio
import aiodocker
import semver

from typing import Dict


class DockerImageCheck(SubSystemCheck):
    """Choose image tag to run for Docker container.

    The image type (``dist``, ``devel``) and version are read from a
    configuration file.  If the configuration file doesn't exist,
    choose a local image that looks reasonable.

    todo::  Read in configuration file
    """

    name = "docker_image"
    fatal = True

    @classmethod
    def add_cl_args(cls, parser):
        parser.add_argument(
            '-i',
            '--image-name',
            help='Full identificator (repository/name:tag) of the image to run',
            dest='image_name',
            action='store',
        )
        parser.add_argument(
            '-r',
            '--pathpilot-repository',
            help='PathPilot Robot repository',
            dest='pathpilot_repository',
            action='store',
        )
        parser.add_argument(
            '-v',
            '--version',
            help='PathPilot Robot image version',
            dest='pathpilot_version',
            action='store',
        )
        parser.add_argument(
            '-ch',
            '--pathpilot-channel',
            help='PathPilot Robot release channel specification',
            dest='pathpilot_channel',
            action='store',
        )
        parser.add_argument(
            '-pc',
            '--pathpilot-configuration',
            help='Name of running configuration',
            dest='pathpilot_configuration',
            metavar='CONFIGURATION',
            action='store',
            type=str,  # Dirty, temporary solution, otherwise special Action would be used
        )

    async def image_available(self, image_name: str) -> bool:
        """Check if image is present and available to local Docker daemon

        Args:
            image_name (str): Full image name to check

        Returns:
            bool: Image present indicator
        """
        async with aiodocker.docker.Docker() as docker:
            for image in await docker.images.list():
                tags = image.get('RepoTags', [])
                if not tags:
                    self.log_info(
                        f'Image {image.get("Id", "UNKNOWN")} has no tags.'
                    )
                    continue
                for tag in tags:
                    if tag == image_name:
                        self.log_info(
                            f'Image {image_name} available on local machine.'
                        )
                        return True
            self.log_warning(f'Image {image_name} is NOT present!')
            return False

    def image_present(self, image_name: str) -> bool:
        """Synchronous wrapper for asynchronous checker if image
        is present and available to local Docker daemon

        Args:
            image_name (str): Full image name to check

        Returns:
            bool: Image present indicator
        """
        return asyncio.run(self.image_available(image_name))

    def any_compat_img(self):
        local_images = PPRosLocalImageVersion.all_images()
        image_type = os.environ.get(
            "IMAGE_TYPE", self.get_cl_or_config('image_type', default='dist')
        )
        compatible_images = [
            i for i in local_images if i.image_type == image_type
        ]
        if not compatible_images:
            self.log_warning(
                "Unable to find Docker images of type %s on local machine"
                % image_type
            )
            return None
        return max(compatible_images)

    def save_image_data(self, image):
        self.set_config('image_name', str(image.image_name))
        self.set_cache(
            'image_type', 'dist' if '-dist-' in image.image_name else 'devel'
        )

    async def check_pathpilot_version(
        self,
        pathpilot_repository: str,
        pathpilot_channel: str,
        pathpilot_version: semver.VersionInfo,
    ) -> bool:
        try:
            pathpilot_channels = pathpilot_versions.PathPilotChannels(
                pathpilot_repository
            )
        except InvalidRegistryInformationError:
            self.log_warning(f'Registry "{pathpilot_repository}" is unknown!')
            return False

        channels = await pathpilot_channels.get_channels(check_nonlocal=False)

        # Should not return more than one with one name
        channel = [ch for ch in channels if ch.name == pathpilot_channel]
        if not channel:
            self.log_warning(
                f'Channel "{pathpilot_channel}" could not be found!'
            )
            return False
        if len(channel) > 1:
            self.log_warning(f'Channels found "{channel}"! This is not right!')
            return False
        channel = channel[0]

        images = await channel.local_channel.get_all_images()
        if not images:
            self.log_warning(
                f'Images for version "{pathpilot_version}" could not be found!'
            )
            return False
        version = [i for i in images if i.version == pathpilot_version]
        if not version:
            self.log_warning(
                f'Version "{pathpilot_version}" could not be found!'
            )
            return False
        if len(version) > 1:
            self.log_warning(
                f'Too many images for version "{pathpilot_version}" found!'
            )
            return False

        version = version[0]
        self.save_image_data(version.name)
        return True

    def run_check(self):
        if 'VIRTUAL_PATHPILOT' in os.environ:
            # Don't run these checks in robot UI; just add stub results
            return True

        image_name, image_src = self.get_cl_or_config(
            'image_name', default=None, return_source=True
        )
        pathpilot_repository = self.get_cl_or_config(
            'pathpilot_repository', default=None
        )
        pathpilot_channel = self.get_cl_or_config(
            'pathpilot_channel', default=None
        )
        pathpilot_version = self.get_cl_or_config(
            'pathpilot_version', default=None
        )

        if (
            pathpilot_repository and pathpilot_channel and pathpilot_version
        ) is not None:
            return asyncio.run(
                self.check_pathpilot_version(
                    pathpilot_repository, pathpilot_channel, pathpilot_version
                )
            )

        if (
            pathpilot_repository or pathpilot_channel or pathpilot_version
        ) is not None:
            self.log_warning(
                "One or more of the required arguments was not passed correctly!"
                f"--pathpilot-repository: '{pathpilot_repository}' "
                f"--pathpilot-channel: '{pathpilot_channel}' "
                f"--pathpilot-version: '{pathpilot_version}'"
            )
            return False

        if image_name is not None:
            self.log_info(f"Image '{image_name}' selected from {image_src}")
            return self.image_present(image_name)

        # Fallback here to the old logic:

        local_images = PPRosLocalImageVersion.all_images()
        if not local_images:
            self.log_fatal("Unable to find Docker images on local machine")
            return False

        # If --tag given, try to use that, otherwise a fallback image
        image_tag, src = self.get_cl_or_config(
            'image_tag', default='dist', return_source=True
        )
        if image_tag is not None:
            self.log_info(f'Image tag taken from {image_tag}:  {src}')
            imgs = [i for i in local_images if i.image_tag == image_tag]
            if len(imgs) == 0:
                fallback_img = self.any_compat_img()
                if fallback_img is None:
                    self.log_fatal(
                        "Specified tag '%s' absent and no fallback local images found"
                        % image_tag
                    )
                    return False
                else:
                    self.log_warning(
                        "Specified tag '%s' absent; using fallback image %s"
                        % (image_tag, fallback_img.image_tag)
                    )
                    self.save_image_data(fallback_img)
                    return True
            elif len(imgs) > 1:  # Is this possible?
                self.log_fatal(
                    "Specified tag '%s' has multiple matches" % image_tag
                )
                return False
            else:  # Found tag
                img = imgs[0]
                self.log_info('Selecting specified image tag "%s"' % image_tag)
                self.save_image_data(img)
                return True

        # Other options select from images with image_type

        image_type = self.get_cl_arg('image_type', 'dist')
        compatible_images = [
            i for i in local_images if i.image_type == image_type
        ]
        if not compatible_images:
            self.log_fatal(
                "Unable to find Docker images of type %s on local machine"
                % image_type
            )
            return False

        # If --image-version given, try to find an image with matching
        # version and type
        image_version = self.get_cl_arg('image_version')
        if image_version is not None:
            image = PPRosLocalImageVersion.image_by_version(
                image_version, image_type
            )
            if image is None:
                self.log_fatal(
                    "Unable to find Docker image version %s on local machine"
                    % image_version
                )
                return False
            self.log_info(
                "Found configured Docker image version %s" % image.image_version
            )
            self.save_image_data(image)
            return True

        # Otherwise, find image with latest version and matching type
        image = max(compatible_images)
        self.log_info(
            "Using discovered Docker image version %s" % image.image_version
        )
        self.save_image_data(image)
        return True

    def docker_run_args(self):
        if not self.get_cache('result') or not self.get_config('image_name'):
            return dict()
        else:
            return dict(image=self.get_config('image_name'))

    def docker_run_environment(self) -> Dict:
        environment = dict()
        image_type = (
            self.get_cache('image_type')
            if self.have_cache('image_type')
            else 'dist'
        )
        if (
            os.environ.get("ROS_SETUP", None) is not None
            and image_type != 'dist'
        ):
            environment.update({'ROS_SETUP': os.environ["ROS_SETUP"]})

        pathpilot_configuration = self.get_cl_arg('pathpilot_configuration')
        if pathpilot_configuration is not None:
            environment.update({'ROBOT_CONFIGURATION': pathpilot_configuration})

        return environment


class DockerRunArgs(SubSystemCheck):
    """Convert command-line args into ``docker run`` args"""

    name = 'docker_run_args'
    depends = "docker_image"

    @classmethod
    def add_cl_args(cls, parser):
        import argparse  # For SUPPRESS, REMAINDER attrs

        parser.add_argument(
            '-n',
            '--name',
            help=(
                'Set the name of the Docker container and the '
                'hostname inside it'
            ),
            type=str,
        )
        parser.add_argument(
            '-l', '--link', help='Link to the named container', type=str
        )
        parser.add_argument(
            'cmd',
            metavar='cmd [args...]',
            help=(
                'Run shell command (with optional args) inside of container '
                '(default: interactive shell)'
            ),
            default=argparse.SUPPRESS,
            nargs=argparse.REMAINDER,
        )
        parser.add_argument(
            '--launcher',
            help='Run robot launcher in container',
            action='store_true',
        )

    def run_check(self):
        # Compute docker_run_args in the check for meaningful status
        # messages
        link = self.get_cl_or_config('link')
        default_name = 'ros-{}-{}'.format(
            self.get_config('image_type'),
            'launch' if self.get_cl_arg('launcher') else 'ui',
        )
        name = self.get_cl_or_config('name', default_name)
        self.dr_args = dr_args = dict(
            # Container name and hostname
            name=name,
            hostname=name,
            # Container links
            links={link: link} if link else dict(),
            # Container command
            command=self.get_cl_arg('cmd', default=None),
            # Run init that reaps processes
            init=True,
            # Use host networking
            network_mode='host',
            # Run in privileged mode
            privileged=True,
            # Don't remove container when finished
            remove=False,
            # Detach
            detach=True,
            # Keep stdin open
            stdin_open=True,
            # Don't use tty; causes log buffering problems
            tty=False,
        )
        if self.get_cl_arg('launcher'):
            self.dr_env = dict(LAUNCHER='1')
        else:
            self.dr_env = dict(ROBOT_UI='1')
        self.dr_vols = self.docker_volume_param('/var/run/docker.sock')

        self.log_info('Using container name "%s"' % dr_args['name'])
        if link:
            self.log_info('Linking container "%s"' % link)
        if self.get_cl_arg('cmd'):
            self.log_info(
                'Running command "%s"' % ' '.join(self.get_cl_arg('cmd'))
            )
        else:
            self.log_info('Running default command')

        # Always passes
        # TODO:  Check linked container exists?
        return True

    def docker_run_args(self):
        # self.dr_args may not be set if dependency failed
        return getattr(self, 'dr_args', dict())

    def docker_run_environment(self):
        # self.dr_env may not be set if dependency failed
        return getattr(self, 'dr_env', dict())

    def docker_run_volumes(self):
        # self.dr_env may not be set if dependency failed
        return getattr(self, 'dr_vols', dict())


class DockerImage(SubSystem):
    """Choose image tag to run for Docker container.

    The image type (``dist``, ``devel``) and version are read from a
    configuration file.  If the configuration file doesn't exist,
    choose a local image that looks reasonable.
    """

    name = "docker_image"

    check_classes = [DockerImageCheck, DockerRunArgs]

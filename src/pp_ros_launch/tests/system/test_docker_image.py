import pytest
import aiodocker
from unittest.mock import MagicMock, patch
from pp_ros_launch.system.docker_image import DockerImageCheck, DockerImage
from .test_subsystem import TestSubSystemCheck, TestSubSystem


@pytest.fixture
def mock_aiodocker_local(request, mock_container_env):
    inst = request.instance

    print('Patching aiodocker client for listing local Docker images')

    async def list_images():
        local_images = [
            {'RepoTags': [f'{inst.docker_repo}:{i}']}
            for i, _, _ in inst.test_docker_tags
        ] + [
            {'RepoTags': None}
        ]  # Special case to test agains the 'none:none' tag
        # TODO: Redo this so it is defined with the rest of tags
        return local_images

    inst.aiodocker_client = aiodocker_client = MagicMock(
        spec=aiodocker.docker.Docker
    )

    aiodocker_client.__aenter__.return_value.images.list.side_effect = (
        list_images
    )

    patch('aiodocker.docker.Docker', return_value=aiodocker_client).start()

    yield aiodocker_client
    patch.stopall()


class TestDockerImageCheck(TestSubSystemCheck):
    test_class = DockerImageCheck
    # Fix PPRosLocalImageVersion class attrs set from environment
    patch_versions_module = True

    cl_args = dict(image_tag=None, image_type='dist', image_version=None)

    @pytest.fixture()
    def obj_pass(self, mock_docker_local, mock_aiodocker_local, mock_cl_args):
        for obj in self.obj_fixture(clear_stash=False):
            obj.set_stash('cl_args', mock_cl_args)
            yield obj

    @pytest.fixture()
    def obj_fail(self, mock_docker_local, mock_aiodocker_local, mock_cl_args):
        self.test_docker_tags = []
        for obj in self.obj_fixture(clear_stash=False):
            obj.set_stash('cl_args', mock_cl_args)
            yield obj


class TestDockerImage(TestSubSystem):
    test_class = DockerImage
    patch_versions_module = True
    cl_args = dict(
        image_tag=None, image_type='dist', image_version=None, cmd=None
    )

    check_test_classes = [TestDockerImageCheck]

    @pytest.fixture()
    def obj_pass(self, mock_docker_local, mock_aiodocker_local, mock_cl_args):
        for obj in self.obj_fixture():
            obj.set_stash('cl_args', mock_cl_args)
            yield obj

    @pytest.fixture()
    def obj_fail(self, mock_docker_local, mock_aiodocker_local, mock_cl_args):
        self.test_docker_tags = []
        for obj in self.obj_fixture():
            obj.set_stash('cl_args', mock_cl_args)
            yield obj

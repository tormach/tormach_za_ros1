import pytest
import sys

if sys.version_info[0] == 2:
    FileNotFoundError = IOError


class TestFixtures:
    test_file_data = 'test file data\n1\n2\n3\n'
    test_file_path = '/tmp/file_data'

    test_file_path_bogus = '/bogus_path/bogus'
    test_file_path_real = '/etc/fstab'

    env = dict(FOO='bar')

    def test_fixture_env(self, mock_env):
        from os import environ

        # Check the basics
        assert hasattr(self, 'env')
        assert len(self.env) == 2  # FOO and PYTEST_CURRENT_TEST

        # Check values set from class
        assert environ['FOO'] == 'bar'

        # Set and test
        self.env['MY_ENV_VAR'] = '42'
        assert 'MY_ENV_VAR' in environ
        assert environ['MY_ENV_VAR'] == '42'

    def test_fixture_open(self, mock_open):
        self.file_data[self.test_file_path] = self.test_file_data
        self.file_data[self.test_file_path_bogus] = None

        # os.path.exists()
        import os

        assert os.path.exists(self.test_file_path)
        assert not os.path.exists(self.test_file_path_bogus)

        # open() existing fake path for reading
        with open(self.test_file_path) as f:
            assert self.test_file_path in self.file_objs

        # open() nonexisting fake path for reading
        with pytest.raises(FileNotFoundError):
            open(self.test_file_path_bogus)

        # open() real path for writing
        with open(self.test_file_path_real) as f:
            assert self.test_file_path in self.file_objs

        # open() and read()
        with open(self.test_file_path) as f:
            assert f.read() == self.test_file_data

        # open() and write()
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_file_data)
            print(self.file_objs[self.test_file_path].getvalue())
            assert (
                self.file_objs[self.test_file_path].getvalue()
                == self.test_file_data
            )
        assert self.file_data[self.test_file_path] == self.test_file_data

    def test_fixture_time(self, mock_time):
        import time

        # Default returns 0, 1, 2, ..., 99
        for i in range(100):
            assert time.time() == i

        # Ideally should include a test that sets `times` attribute...

    def test_fixture_requests(self, mock_requests):
        import requests

        # Only the `get()` method is mocked
        url = 'http://example.com'
        headers = dict(h1='h1')
        rsp = requests.get(url, headers=headers)
        print('reqs:', self.reqs)
        assert url in self.reqs
        for key, val in headers.items():
            assert self.reqs[url][key] == val
        assert rsp is self.reqs[url]['rsp']
        json_rsp = rsp.json()
        print('json_rsp:', json_rsp)
        assert json_rsp['expires_in'] == 50
        assert 'token' in json_rsp

    def test_fixture_find_executable(self, mock_find_executable):
        import distutils.spawn

        executable = 'myprogram'
        path = '/usr/bin/' + executable
        self.executable_map[executable] = path
        assert distutils.spawn.find_executable(executable) == path

        self.executable_map.pop(executable)
        assert distutils.spawn.find_executable(executable) is None

    def test_fixture_subprocess_popen(self, mock_subprocess_popen):
        import subprocess

        res = subprocess.Popen()
        assert res is mock_subprocess_popen
        self.mock_popen.assert_called()

    def test_fixture_termios(self, mock_termios):
        import termios

        # Test success, default
        self.have_tty = True
        assert hasattr(self, 'tcgetattr_res')
        res = termios.tcgetattr(1)
        print("success/default calls:", self.termios.mock_calls)
        self.termios.tcgetattr.assert_called_with(1)
        assert res == self.tcgetattr_res
        self.termios.reset_mock()

        # Test success, custom
        self.have_tty = True
        self.tcgetattr_res = [42, 13]
        res = termios.tcgetattr(2)
        print("success/custom calls:", self.termios.mock_calls)
        self.termios.tcgetattr.assert_called_with(2)
        assert res == self.tcgetattr_res
        self.termios.reset_mock()

        # Test failure
        self.have_tty = False
        assert hasattr(self, 'termios_error')
        with pytest.raises(self.termios_error):
            termios.tcgetattr(3)
        print("success/custom calls:", self.termios.mock_calls)
        self.termios.tcgetattr.assert_called_with(3)

    def test_fixture_uid_gid(self, mock_uid_gid):
        import os

        # Test defaults
        assert os.getuid() == 1000
        assert os.getgid() == 1000

        # Test custom
        self.uid = 42
        self.gid = 13
        assert os.getuid() == 42
        assert os.getgid() == 13

    def test_fixture_cwd(self, mock_cwd):
        import os

        # Test default
        assert os.getcwd() == '/home/pathpilot'
        mock_cwd.assert_called()
        mock_cwd.reset_mock()

        # Test custom
        self.cwd = '/tmp/foo'
        assert os.getcwd() == '/tmp/foo'
        mock_cwd.assert_called()
        mock_cwd.reset_mock()

    def test_fixture_groups(self, mock_groups):
        import os
        import grp

        # Test grp.getgrnam defaults
        assert grp.getgrnam('docker').gr_gid == 801

        # Test os.getgroups defaults
        assert os.getgroups() == [24, 25, 27, 29, 30, 801, 802, 803, 1000]

        # Test grp.getgrnam custom
        self.sys_groups = dict(bogus_group=42)
        assert grp.getgrnam('bogus_group').gr_gid == 42

        # Test os.getgroups custom
        self.group_ids = [13, 42]
        assert os.getgroups() == [13, 42]

        # Test nonexistent GID
        with pytest.raises(KeyError):
            grp.getgrnam('absent_group')

    # --------------
    # Docker

    test_env_vars = (
        'ROS_DISTRO',
        'DEBIAN_SUITE',
        'IMAGE_VERSION',
        'IMAGE_TYPE',
        'DOCKER_REPO',
    )

    # Patch pp_ros_launch.image.versions.PPRosImageVersion attributes
    patch_versions_module = True
    image_version_major = 13
    image_version_hash = 'babababa'
    image_version_expected = f'{image_version_major}+{image_version_hash}'

    def test_fixture_container_env(self, mock_container_env):
        import os

        # Check the basics
        for attr in self.test_env_vars:
            assert hasattr(self, attr.lower())
            assert attr in os.environ

        # Specific attributes
        assert os.environ['DOCKER_REPO'] == self.docker_repo
        assert os.environ['IMAGE_TYPE'] == 'dist'

        # Test pp_ros_launch.image.versions.PPRosImageVersion
        from pp_ros_launch.image.versions import PPRosImageVersion

        assert self.image_version == self.image_version_expected
        assert PPRosImageVersion.IMAGE_VERSION == self.image_version_expected

    def test_fixture_docker_local(self, mock_docker_local):
        import docker

        # Attributes
        assert docker.__version__[0] >= 6

        # Client object
        client = docker.from_env()
        assert client is mock_docker_local
        assert client is self.docker_client

        # Client images.list()
        for obj in client.images.list():
            assert isinstance(obj.tags, list)
            assert len(obj.tags) == 3
            assert obj.tags[2] == 'bogus'

        # Client images.get()
        image = ':'.join([self.docker_repo, self.tag])
        assert client.images.get(image) is self.get_rv

    def test_fixture_docker_hub(self, mock_docker_hub):
        from pp_ros_launch.image.docker_hub import DockerRepo

        dr = DockerRepo(self.docker_repo)
        assert dr.get_tags_list() == [t[0] for t in self.test_docker_tags]
        assert dr.get_labels('bogus_reference') == self.labels

import pytest
from pp_ros_launch.system.user import User, UidGidHome, UserMediaDirCheck
from .test_subsystem import (
    TestSubSystem,
    TestSubSystemCheck,
    TestSubSystemDockerMountCheck,
)


class TestUidGidHome(TestSubSystemCheck):
    test_class = UidGidHome
    always_passes = True
    user = 'pathpilot'
    home = '/home/pathpilot'
    expected_environment = dict(UID='1000', GID='1000', USER=user, HOME=home)

    @pytest.fixture()
    def obj_pass(self, mock_env, mock_uid_gid):
        self.env['USER'] = self.user
        self.env['HOME'] = self.home
        yield from self.obj_fixture()

    def test_cached_result(self, obj_pass):
        assert obj_pass.check_result is True
        for attr, val in (
            ('uid', 1000),
            ('gid', 1000),
            ('user', self.user),
            ('home', self.home),
        ):
            assert obj_pass.have_cache(attr)
            assert obj_pass.get_cache(attr) == val


class TestUserMediaDirCheck(TestSubSystemDockerMountCheck):
    test_class = UserMediaDirCheck
    always_passes = True
    user = 'pathpilot'
    user_media = '/media/pathpilot'
    mount_type = 'bind'
    read_only = False
    propagation = 'shared'
    expected_mounts = {
        'Target': user_media,
        'Source': user_media,
        'Type': mount_type,
        'ReadOnly': read_only,
        'BindOptions': {'Propagation': propagation},
    }

    @pytest.fixture()
    def obj_pass(self, mock_open):
        self.file_data.update({self.user_media: ''})
        yield from self.obj_fixture()

    def test_cached_result(self, obj_pass):
        assert obj_pass.check_result is True


class TestUser(TestSubSystem):
    test_class = User
    always_passes = True
    check_test_classes = [TestUidGidHome, TestUserMediaDirCheck]

    @pytest.fixture()
    def obj_pass(self, mock_env, mock_uid_gid, mock_open):
        tc = self.check_test_classes[0]
        self.env['USER'] = tc.user
        self.env['HOME'] = tc.home
        self.file_data = {'/media/pathpilot': ''}
        yield from self.obj_fixture()

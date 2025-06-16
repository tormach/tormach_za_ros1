import pytest
import yaml
from unittest.mock import patch, MagicMock
from pp_ros_launch.config import PPROSContainerConfig
from pp_ros_launch.image.versions import PPRosLocalImageVersion


class TestPPROSContainerConfig:
    tc = PPROSContainerConfig
    ivc = PPRosLocalImageVersion

    def test_attrs(self):
        assert self.tc.default_state_path().endswith('.yaml')
        assert isinstance(self.tc.name, str)

    @pytest.fixture
    def obj(self, mock_open, mock_docker_local):
        self.tc.clear_stash()  # Make sure stash/cache is fresh

        # Test config file
        self.test_data = dict(image_tag=self.tag, other_opt='bogus other opt')
        self.test_file_data = yaml.dump(
            self.test_data, default_flow_style=False
        )
        self.file_data[self.tc.default_state_path()] = self.test_file_data

        # Test command line arguments
        class cl_arg_class:
            pass

        self.cl_args = cl_arg_class()
        self.cl_args.state_file = self.tc.default_state_path()

        # Test class instance
        with patch.object(self.ivc, 'docker_client', mock_docker_local):
            yield self.tc()

    def test_fixture_obj(self, obj):
        import os

        # test object attributes
        assert self.tc.default_state_path() in self.file_data
        assert (
            self.file_data[self.tc.default_state_path()] == self.test_file_data
        )

        # os.path.exists()
        assert os.path.exists(self.tc.default_state_path())

        # open()
        with open(self.tc.default_state_path()) as f:
            assert f.read() == self.test_file_data

        # test_data
        print('tag:', self.tag)
        assert self.ivc.is_valid_image_tag(self.tag)

        # cl_args
        assert self.cl_args.state_file == self.tc.default_state_path()

        # PPRosLocalImageVersion Docker client
        assert self.ivc.docker_client is self.docker_client

    def test_logger(self, obj):
        assert hasattr(obj.logger, 'info')
        assert hasattr(self.tc.cls_logger(), 'info')

    def test_stash(self, obj):
        # Test setting from class, and getting from class & instance
        self.tc.set_stash('foo', 42)
        assert self.tc.get_stash('foo') == 42
        assert obj.get_stash('foo') == 42

        # Test setting from instance, and getting from class & instance
        obj.set_stash('bar', 13)
        assert self.tc.get_stash('bar') == 13
        assert obj.get_stash('bar') == 13
        assert obj.get_stash('foo') == 42  # Sanity

        # Test redefining a key
        obj.set_stash('foo', 99)
        assert obj.get_stash('foo') == 99
        assert self.tc.get_stash('foo') == 99

        # Test getting unset value
        assert obj.get_stash('bogus') is None
        assert self.tc.get_stash('bogus') is None

        # Test clearing stash
        self.tc.clear_stash()
        assert obj.get_stash('foo') is None
        assert obj.get_stash('bar') is None
        assert self.tc.get_stash('foo') is None

    def test_state_path(self):
        assert self.tc.get_stash('state_path') is None  # Sanity

        # Test setting state_path from class only
        state_path = '/tmp/foo'
        self.tc.set_state_path(state_path)
        assert self.tc.get_stash('state_path') == state_path
        assert self.tc.get_state_path() == state_path

        # Test instance state path
        obj = self.tc()
        assert obj.get_state_path() == state_path

        # Test state path set through object instantiation
        state_path = '/tmp/bar'
        obj = self.tc(state_path=state_path)
        assert obj.get_state_path() == state_path
        assert self.tc.get_state_path() == state_path

    def test_init(self):
        # Test default state_path
        self.tc.clear_stash()
        obj = self.tc()
        assert obj.get_state_path() == self.tc.default_state_path()

        # Test supplied state_path
        self.tc.clear_stash()
        state_path = '/tmp/baz'
        obj = self.tc(state_path=state_path)
        assert obj.get_state_path() == state_path
        assert self.tc.get_state_path() == state_path

    def test_add_cl_state_fil_arg(self):
        mock_parser = MagicMock()
        self.tc.add_cl_state_file_arg(mock_parser)
        mock_parser.add_argument.assert_called()

    def test_read_config(self, obj):
        # Test default file path
        assert obj.read_config() == self.test_data
        assert self.tc.read_config() == self.test_data

        # Test nonexistent file path
        bogus_obj = self.tc('bogus')
        assert bogus_obj.read_config() == dict()

    def test_write_config(self, obj):
        # No/empty config read raises an exception
        assert not obj.config  # Sanity
        with pytest.raises(RuntimeError):
            obj.write_config()

        # Set config and write
        assert obj.read_config() == self.test_data
        obj.write_config()
        print(
            "Written config file:", self.file_data[self.tc.default_state_path()]
        )
        assert (
            self.file_data[self.tc.default_state_path()] == self.test_file_data
        )

    def test_config_init(self, obj, mock_open):
        self.cl_args.state_file = '/tmp/foo'
        self.file_data['/tmp/foo'] = 'foo: 42\n'

        # Test init_config()
        self.tc.init_config(self.cl_args)
        assert self.tc.get_stash('cl_args') is self.cl_args
        assert self.tc.get_state_path() == self.cl_args.state_file
        config = self.tc.get_stash('config')
        assert len(config) == 1
        assert config['foo'] == 42

        # Test _clear_config()
        config = self.tc._clear_config()
        assert config == dict()
        assert self.tc.get_stash('config') is config

    def test_config_attr(self, obj):
        # Test uninitialized
        assert not obj.config

        # Set up & verify test
        assert obj.read_config() == self.test_data

        # Test config attribute
        assert obj.config == self.test_data

    def test_get_set_config(self, obj):
        # Test setting and getting
        obj.set_config('foo', 42)
        assert 'foo' in obj.config
        assert obj.config['foo'] == 42
        assert obj.get_config('foo') == 42

        # Test getting uninitialized & default
        assert obj.get_config('bar') is None
        assert obj.get_config('baz', 17) == 17

    def test_cl_args(self, obj):
        # Setup
        cl_arg = 'my command-line arg'
        self.cl_args.other_opt = cl_arg
        print(self.cl_args.__dict__)
        assert self.cl_args.__dict__['other_opt'] == cl_arg
        obj.init_config(self.cl_args)

        # Test cl_args property
        assert obj.cl_args is self.cl_args

        # Test get_cl_arg()
        assert obj.get_cl_arg('other_opt') == cl_arg
        assert obj.get_cl_arg('bogus_opt') is None
        assert obj.get_cl_arg('bogus_opt', 88) == 88

    def test_get_cl_or_config(self, obj):
        # Set up overriding and non-conflicting command line args
        cl_arg_override = 'my overriding command-line arg'
        self.cl_args.other_opt = cl_arg_override
        cl_arg_noconflict = 'my non-conflicting command-line arg'
        self.cl_args.this_opt = cl_arg_noconflict
        obj.init_config(self.cl_args)

        # Test override
        assert obj.get_cl_or_config('other_opt', return_source=True) == (
            cl_arg_override,
            'command line',
        )
        assert obj.get_cl_or_config('other_opt') == cl_arg_override

        # Test non-conflicting
        assert obj.get_cl_or_config('this_opt', return_source=True) == (
            cl_arg_noconflict,
            'command line',
        )
        assert obj.get_cl_or_config('this_opt') == cl_arg_noconflict

        # Test absent option
        assert obj.get_cl_or_config('bogus') is None
        assert obj.get_cl_or_config('bogus', 66, return_source=True) == (
            66,
            'default',
        )
        assert obj.get_cl_or_config('bogus', 66) == 66

        # Test config-only option
        obj.set_config('config_only_option', 22)
        assert obj.get_cl_or_config(
            'config_only_option', return_source=True
        ) == (22, 'state file')
        assert obj.get_cl_or_config('config_only_option') == 22

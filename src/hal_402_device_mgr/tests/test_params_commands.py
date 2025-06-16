import pytest
from unittest.mock import MagicMock, patch
from hal_402_device_mgr.params.commands import EtherCATCommand


class TestEtherCATCommandBase:
    commands = [
        'upload',
        'download',
        'master',
        'slaves',
        'debug',
        'version',
        'xml',
    ]

    @pytest.fixture
    def cmd(self):
        # Clean up any instances and return cmd
        EtherCATCommand._command_instances = dict()
        yield EtherCATCommand()

    def test_command_registry(self):
        # Check that the expected commands were registered, no more, no less
        # (Do it this wacky way to show exactly what's missing on failure)
        for command in self.commands:
            assert command in EtherCATCommand._command_registry
        for command in EtherCATCommand._command_registry:
            assert command in self.commands

        # Sanity check the registry classes
        for command in self.commands:
            command_class = EtherCATCommand._command_registry[command]
            assert issubclass(command_class, EtherCATCommand)
            assert command_class.command == command

    def test_get_command_instance(self, cmd):
        assert len(cmd._command_instances) == 0

        inst1 = cmd._get_command_instance('upload')
        assert len(cmd._command_instances) == 1

        inst2 = cmd._get_command_instance('upload')
        assert len(cmd._command_instances) == 1
        assert inst1 is inst2

        inst3 = cmd._get_command_instance('debug')
        assert len(cmd._command_instances) == 2
        assert inst1 is not inst3

    def test_resolve_options_flags(self, cmd):
        # Test data,  3-tuple of:
        # - dict of given command flag options (may be empty)
        # - dict of option defaults (may be empty)
        # - list of resulting command-line options (sorted)
        data = [
            # empty, no defaults
            (dict(), dict(), list()),
            # empty, default false
            (dict(), dict(false1=False, false2=False), list()),
            # empty, default true
            (dict(), dict(true1=True, true2=True), ['--true1', '--true2']),
            # empty, default some true, some false
            (
                dict(),
                dict(false1=False, true1=True, true2=True, false2=False),
                ['--true1', '--true2'],
            ),
            # set one,  default some true, some false
            (
                dict(false1=1),
                dict(false1=False, true1=True, true2=True, false2=False),
                ['--false1', '--true1', '--true2'],
            ),
            # set three,  default some true, some false
            (
                dict(false1=1, false2=1, true2=1),
                dict(false1=False, true1=True, true2=True, false2=False),
                ['--false1', '--false2', '--true1', '--true2'],
            ),
            # set & unset,  default some true, some false
            (
                dict(false1=1, false2=0, true1=1, true2=0),
                dict(false1=False, true1=True, true2=True, false2=False),
                ['--false1', '--true1'],
            ),
        ]

        for kwargs, option_defaults, expected_results in data:
            results = sorted(cmd._resolve_options(kwargs, option_defaults))
            assert results == expected_results
            assert len(kwargs) == 0

    def test_resolve_options_args(self, cmd):
        # Test data,  3-tuple of:
        # - dict of given command arg options (may be empty)
        # - dict of option defaults (may be empty)
        # - list of resulting command-line options (sorted)
        data = [
            # empty, defaults empty
            (dict(), dict(arg1=None, arg2=None), list()),
            # empty, defaults populated
            (dict(), dict(arg1='a1', arg2='a2'), ['--arg1=a1', '--arg2=a2']),
            # one option, defaults empty
            (dict(arg1='a1'), dict(arg1=None, arg2=None), ['--arg1=a1']),
            # one option, defaults populated
            (
                dict(arg1='b1'),
                dict(arg1='a1', arg2='a2'),
                ['--arg1=b1', '--arg2=a2'],
            ),
            # two options, defaults populated
            (
                dict(arg1='b1', arg2='b2'),
                dict(arg1='a1', arg2='a2'),
                ['--arg1=b1', '--arg2=b2'],
            ),
            # clear option, defaults populated
            (dict(arg1=None), dict(arg1='a1', arg2='a2'), ['--arg2=a2']),
        ]

        for kwargs, option_defaults, expected_results in data:
            results = sorted(cmd._resolve_options(kwargs, option_defaults))
            assert results == expected_results
            assert len(kwargs) == 0

    def test_resolve_options(self, cmd):
        # Test data,  3-tuple of:
        # - dict of given command options (may be empty)
        # - dict of option defaults (may be empty)
        # - list of resulting command-line options (sorted)
        data = [
            (
                dict(),
                dict(
                    arg1='a1', arg2=None, false1=False, true1=True, true2=True
                ),
                ['--arg1=a1', '--true1', '--true2'],
            ),
            (
                dict(arg1='b1', arg2='b2', false1=1, true2=False),
                dict(
                    arg1='a1', arg2=None, false1=False, true1=True, true2=True
                ),
                ['--arg1=b1', '--arg2=b2', '--false1', '--true1'],
            ),
        ]

        for kwargs, option_defaults, expected_results in data:
            results = sorted(cmd._resolve_options(kwargs, option_defaults))
            assert results == expected_results
            assert len(kwargs) == 0

    def test_resolve_options_partial(self, cmd):
        # Test that partial resolution of options leaves unused
        # options in kwargs
        kwargs = dict(
            arg1='b1', arg2='b2', arg3='b3', false1=1, flag3=1, true2=False
        )
        option_defaults = dict(
            arg1='a1', arg2=None, false1=False, true1=True, true2=True
        )
        res = cmd._resolve_options(
            kwargs,
            option_defaults,
        )

        assert sorted(res) == ['--arg1=b1', '--arg2=b2', '--false1', '--true1']
        assert sorted(kwargs.keys()) == ['arg3', 'flag3']

    def test_resolve_command_arguments(self, cmd):
        # Test data,  3-tuple of:
        # - list of given command arguments (may be empty)
        # - list of argument specs (may be empty)
        # - list of resulting command-line options
        data = [
            # empty; empty specs
            (list(), dict(), list()),
            # empty; optional specs
            (
                list(),
                [
                    dict(name='arg1', optional=True),
                    dict(name='arg2', optional=True),
                ],
                list(),
            ),
            # two args; non-optional specs
            (
                ['a1', 'a2'],
                [dict(name='arg1'), dict(name='arg2')],
                ['a1', 'a2'],
            ),
            # two args; three mixed-optional specs (`ethercat download`)
            (
                ['a1', 'a3'],
                [
                    dict(name='arg1'),
                    dict(name='arg2', optional=True),
                    dict(name='arg3'),
                ],
                ['a1', 'a3'],
            ),
            # two args; formatters
            (
                [12648430, 3735928559],
                [dict(name='arg1', conv=hex), dict(name='arg2', conv=hex)],
                ['0xc0ffee', '0xdeadbeef'],
            ),
            # two args; formatters & mixed-optional specs (`ethercat download`)
            (
                [12648430, 3735928559],
                [
                    dict(name='arg1', conv=hex),
                    dict(name='arg2', optional=True, conv=hex),
                    dict(name='arg3'),
                ],
                ['0xc0ffee', '3735928559'],
            ),
        ]
        for args, argument_specs, expected_results in data:
            print(f'args:  {args}')
            print(f'argument_specs:  {argument_specs}')
            print(f'expected_results:  {expected_results}')
            actual_results = sorted(
                cmd._resolve_command_arguments(args, argument_specs)
            )
            print(f'actual_results:  {actual_results}')
            assert actual_results == expected_results
            print()

    def test_global_options(self, cmd):
        # Test data,  2-tuple of:
        # - dict of given command flag options (may be empty)
        # - list of resulting command-line options (sorted)
        global_options_data = [
            # empty
            (dict(), list()),
            # set master
            (dict(master=0), ['--master=0']),
            # set verbose
            (dict(verbose=1), ['--verbose']),
            # set all flags
            (
                dict(verbose=1, force=1, quiet=1),
                ['--force', '--quiet', '--verbose'],
            ),
            # set master & verbose
            (dict(verbose=1, master='-'), ['--master=-', '--verbose']),
        ]

        for kwargs, expected_results in global_options_data:
            results = sorted(cmd.global_options(kwargs))
            assert results == expected_results
            assert len(kwargs) == 0


class TestEtherCATUpload:
    command = 'upload'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (
            dict(position=1, type='uint16', verbose=1),
            [0x2002, 0x01],
            ['--verbose', '--position=1', '--type=uint16', '0x2002', '0x01'],
        ),
        (
            dict(position=5, type='int32'),
            [0x1401],
            ['--position=5', '--type=int32', '0x1401'],
        ),
    ]

    @pytest.fixture
    def base_cmd(self):
        # Clean up any instances and return cmd
        EtherCATCommand._command_instances = dict()
        yield EtherCATCommand()

    @pytest.fixture
    def cmd(self, base_cmd):
        yield base_cmd._get_command_instance(self.command)

    def test_class_attrs(self, cmd):
        assert cmd.command == self.command

        assert hasattr(cmd, 'global_option_defaults')
        assert (
            cmd.global_option_defaults is EtherCATCommand.global_option_defaults
        )

        assert hasattr(cmd, 'command_option_defaults')
        assert isinstance(cmd.command_option_defaults, dict)

        assert hasattr(cmd, 'command_argument_specs')
        assert isinstance(cmd.command_argument_specs, list)
        legal_spec_keys = {'name', 'conv', 'optional'}
        for spec in cmd.command_argument_specs:
            assert 'name' in spec
            for key in spec.keys():
                assert key in legal_spec_keys

    def test_run_args(self, cmd):
        for kwargs, args, expected_results in self.command_data:
            kwargs = kwargs.copy()
            print(f'args:  {args}')
            print(f'kwargs:  {kwargs}')
            print(f'expected_results:  {expected_results}')
            actual_results = cmd.run_args(*args, **kwargs)
            print(f'actual_results:  {actual_results}')
            assert actual_results[:2] == ['ethercat', self.command]
            assert actual_results[2:] == expected_results

    @pytest.fixture
    def check_output(self):
        check_output = MagicMock()
        patch('subprocess.check_output', check_output).start()
        yield check_output
        patch.stopall()

    def test_run(self, cmd, check_output):
        for kwargs, args, expected_results in self.command_data:
            kwargs = kwargs.copy()
            print(f'args:  {args}')
            print(f'kwargs:  {kwargs}')
            expected_command = ['ethercat', self.command] + expected_results
            print(f'expected_command:  {expected_command}')
            cmd.run(*args, **kwargs)
            print(f'subprocess.check_output calls:  {check_output.mock_calls}')
            check_output.assert_called_with(expected_command)
            check_output.reset_mock()  # Clear out list of calls
            print()

    def test_run_command(self, base_cmd, check_output):
        for kwargs, args, expected_results in self.command_data:
            kwargs = kwargs.copy()
            print(f'args:  {args}')
            print(f'kwargs:  {kwargs}')
            expected_command = ['ethercat', self.command] + expected_results
            print(f'expected_command:  {expected_command}')
            base_cmd.run_command(self.command, *args, **kwargs)
            print(f'subprocess.check_output calls:  {check_output.mock_calls}')
            check_output.assert_called_with(expected_command)
            check_output.reset_mock()  # Clear out list of calls
            print()


class TestEtherCATDownload(TestEtherCATUpload):
    command = 'download'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (
            dict(position=1, type='uint16', verbose=1),
            [0x2002, 0x01, 42],
            [
                '--verbose',
                '--position=1',
                '--type=uint16',
                '0x2002',
                '0x01',
                '42',
            ],
        ),
        (
            dict(position=5, type='int32'),
            [0x1401, 13],
            ['--position=5', '--type=int32', '0x1401', '13'],
        ),
    ]


class TestEtherCATMaster(TestEtherCATUpload):
    command = 'master'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (dict(), [], []),
        (dict(master=0), [], ['--master=0']),
    ]


class TestEtherCATSlaves(TestEtherCATUpload):
    command = 'slaves'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (dict(position=5), [], ['--position=5']),
        (dict(master=3, position=7), [], ['--master=3', '--position=7']),
    ]


class TestEtherCATDebug(TestEtherCATUpload):
    command = 'debug'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (dict(), [0], ['0']),
        (dict(master=3), [2], ['--master=3', '2']),
    ]


class TestEtherCATVersion(TestEtherCATUpload):
    command = 'version'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (dict(), [], []),
    ]


class TestEtherCATXML(TestEtherCATUpload):
    command = 'xml'

    # 3-tuples of (command options, command arguments, expected command line)
    command_data = [
        (dict(), [], []),
        (dict(position=5), [], ['--position=5']),
    ]

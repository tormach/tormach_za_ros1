import pytest
from hal_402_device_mgr.params.config_drive import ConfigDrive


class TestConfigDrive:
    @pytest.fixture
    def obj(self):
        yield ConfigDrive()

    def test_parse_argv(self, obj):
        # Test mode args
        obj._parse_argv(['--from-yaml=foo.yaml'])
        assert obj.args.from_yaml == 'foo.yaml'
        obj._parse_argv(['--from-mdb=foo.mdb'])
        assert obj.args.from_mdb == 'foo.mdb'
        obj._parse_argv(['--from-rosparam'])
        assert obj.args.from_rosparam is True
        obj._parse_argv(['--from-slaves=1-3,5'])
        assert obj.args.from_slaves == [1, 2, 3, 5]

        # Test dump-config
        obj._parse_argv(['--from-rosparam', '--dump-config'])
        assert obj.args.dump_config is True
        obj._parse_argv(['--from-rosparam'])
        assert obj.args.dump_config is False

        # Test master
        # - default
        obj._parse_argv(['--from-rosparam', '--dump-config'])
        assert obj.args.master == 0
        # - 4
        obj._parse_argv(['--from-rosparam', '--dump-config', '--master=4'])
        assert obj.args.master == 4

        # Test actual useful commands: `rosrun hal_402_device_mgr drive_config [args]`
        yaml = 'src/tormach/za6_hardware/config/ethercat_drive_params.yaml'
        xml = 'src/tormach/za6_hardware/config/IS620N-Ecat_v2.6.7.xml'
        # - YAML
        obj._parse_argv(
            ['--from-yaml', yaml, '--group', 'joints', '--dump-config']
        )
        assert obj.args.from_yaml == yaml
        assert obj.args.group == 'joints'
        assert obj.args.dump_config is True

        # - MDB
        obj._parse_argv(
            ['--from-mdb=J1.txt', '--drive-xml', xml, '--dump-config']
        )
        assert obj.args.from_mdb == 'J1.txt'
        assert obj.args.drive_xml == xml
        assert obj.args.dump_config is True

        # - Slaves
        obj._parse_argv(
            ['--from-slaves=1-6', '--dump-config', '--drive-xml', xml]
        )
        assert obj.args.from_slaves == [1, 2, 3, 4, 5, 6]
        assert obj.args.drive_xml == xml
        assert obj.args.dump_config is True

        # - Rosparam
        obj._parse_argv(
            ['--from-rosparam', '--group', 'joints', '--dump-config']
        )
        assert obj.args.from_rosparam is True
        assert obj.args.group == 'joints'
        assert obj.args.dump_config is True

        # - Copy from MDB to slave 0
        obj._parse_argv(
            [
                '--from-mdb',
                'J1.txt',
                '--drive-xml',
                xml,
                '--to-slaves=0',
                '--dry-run',
            ]
        )
        assert obj.args.from_mdb == 'J1.txt'
        assert obj.args.drive_xml == xml
        assert obj.args.to_slaves == [0]
        assert obj.args.dry_run is True

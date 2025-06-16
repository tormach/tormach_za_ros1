import argparse
import sys
from .int_range import IntRangeParser
from .params_mdb import EtherCATMDBParams
from .params_drive import EtherCATDriveParams
from .params_yaml import EtherCATYAMLParams
from .params_rospy import EtherCATROSParams


class ConfigDriveCLIError(RuntimeError):
    pass


class ConfigDrive:
    def __init__(self):
        self.params = None

    def _parse_argv(self, argv):
        parser = argparse.ArgumentParser(
            description='Configure an EtherCAT drive'
        )

        # Configuration sources
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument(
            '--from-yaml',
            type=str,
            help='Load configuration from YAML input file',
        )
        mode.add_argument(
            '--from-mdb',
            type=str,
            help='Load configuration from InoServoShop .mdb input file',
        )
        mode.add_argument(
            '--from-rosparam',
            action='store_true',
            help='Load configuration from rosparam server',
        )
        mode.add_argument(
            '--from-slaves',
            type=IntRangeParser.parse,
            help='Load configuration from slave positions, e.g. "1-3,5"',
        )

        # GUID
        mode.add_argument(
            '--set-guid',
            type=IntRangeParser.parse,
            help=(
                'Set drive GUID to slave postions, e.g. "0-5"'
                ' (optional: "--force")'
            ),
        )
        mode.add_argument(
            '--get-guid',
            type=IntRangeParser.parse,
            help='Print drive GUID from slave postions, e.g. "0-5"',
        )

        # NV params
        mode.add_argument(
            '--get-non-volatile',
            type=IntRangeParser.parse,
            help='Get params non-volatile setting at postions e.g. "0-5"',
        )
        mode.add_argument(
            '--set-non-volatile',
            type=IntRangeParser.parse,
            help='Set params non-volatile at postions e.g. "0-5"',
        )
        mode.add_argument(
            '--set-non-volatile-off',
            type=IntRangeParser.parse,
            help='Set params volatile at postions e.g. "0-5"',
        )

        tlk = EtherCATYAMLParams.param_top_level_key
        parser.add_argument(
            '--group',
            type=str,
            help=(
                f'Read group (e.g. "joints") under YAML/rosparam "{tlk}" key'
            ),
        )
        parser.add_argument(
            '--drive-xml',
            type=str,
            default=None,
            help=(
                'Path of drive XML description file '
                '(optional when supplied by YAML or ROS param)'
            ),
        )

        # Configuration destinations
        parser.add_argument(
            '--to-slaves',
            type=IntRangeParser.parse,
            help='Update configuration to slave positions, e.g. "1-3,5"',
        )
        parser.add_argument(
            '--params',
            nargs='+',
            metavar='XXXX-YYh',
            help='(For --to-slaves) limit writes to specified params',
        )
        parser.add_argument(
            '--dump-config',
            action='store_true',
            help='Dump params in YAML format to stdout',
        )

        # General options
        parser.add_argument(
            '--master', type=int, default=0, help='Master to select; default 0'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be written to slaves',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force some commands',
        )

        self.args = parser.parse_args(argv)

    def locate_xml(self):
        """Find XML drive description file path

        File path derived either from command line `--drive-xml` arg
        or else the YAML or ROS params
        """
        if self.args.drive_xml is not None:
            # Path given on command line overrides other sources
            return self.args.drive_xml

        # Query ROS param server
        # - This may throw ConnectionRefusedError
        return EtherCATYAMLParams.rosparams_xml_path(self.args.group)

    def read_mdb(self):
        xml_fname = self.locate_xml()
        self.params = EtherCATMDBParams(self.args.from_mdb, xml_fname)
        self.params.read()

    def read_slaves(self):
        xml_fname = self.locate_xml()
        self.params = EtherCATDriveParams(
            xml_fname, master=self.args.master, positions=self.args.from_slaves
        )
        self.params.read()

    def write_slaves(self):
        try:
            params_out = EtherCATDriveParams.copy(
                self.params,
                xml_fname=None,
                master=self.args.master,
                positions=self.args.to_slaves,
            )
        except ValueError as e:
            sys.stderr.write(f"Error:  {str(e)}\n")
        params_out.write(params=self.args.params, dry_run=self.args.dry_run)

    def _setup_drives(self, positions=None):
        xml_fname = self.locate_xml()
        self.params = EtherCATDriveParams(
            xml_fname, master=self.args.master, positions=positions
        )
        self.params.setup(self.params.query_device_type())
        self.params.read_xml(self.params.xml_fname)

    def get_guid(self, setup=True):
        if setup:
            self._setup_drives(positions=self.args.get_guid)
        for slave in self.params.positions:
            uid = self.params.get_guid(slave)
            if uid:
                print(f"{self.args.master},{slave}:  {uid:012X}")
            else:
                print(f"{self.args.master},{slave}:  UNSET")

    def set_guid(self, setup=True):
        if setup:
            self._setup_drives(positions=self.args.set_guid)
        for slave in self.params.positions:
            self.params.set_guid(
                slave, force=self.args.force, dry_run=self.args.dry_run
            )
        self.get_guid(setup=False)

    def get_non_volatile(self):
        self._setup_drives(positions=self.args.get_non_volatile)
        for slave in self.params.positions:
            val = self.params.get_params_nv(slave)
            print(f"{self.args.master},{slave}:  {val}")

    def set_non_volatile(self, off=False):
        positions = (
            self.args.set_non_volatile_off
            if off
            else self.args.set_non_volatile
        )
        self._setup_drives(positions=positions)
        for slave in positions:
            self.params.set_params_nv(slave, off=off, dry_run=self.args.dry_run)

    def read_yaml(self):
        self.params = EtherCATYAMLParams(self.args.from_yaml, self.args.group)
        self.params.read()

    def read_rosparams(self):
        group = self.args.group
        if group is None:
            raise ConfigDriveCLIError("--from-rosparam requires --group arg")
        self.params = EtherCATROSParams(group)
        self.params.read()

    def cli(self, argv):
        self._parse_argv(argv[1:])

        try:
            if self.args.from_yaml:
                self.read_yaml()
            elif self.args.from_rosparam:
                self.read_rosparams()
            elif self.args.from_mdb:
                self.read_mdb()
            elif self.args.from_slaves:
                self.read_slaves()

            if self.args.to_slaves:
                self.write_slaves()
            if self.args.dump_config:
                self.params.dump()
            if self.args.get_non_volatile:
                self.get_non_volatile()
            if self.args.set_non_volatile:
                self.set_non_volatile()
            if self.args.set_non_volatile_off:
                self.set_non_volatile(off=True)
            if self.args.set_guid:
                self.set_guid()
            if self.args.get_guid:
                self.get_guid()
        except ConfigDriveCLIError as e:
            sys.stderr.write(f"Usage error:  {str(e)}\n")
            sys.exit(1)
        except ConnectionRefusedError as e:
            sys.stderr.write(f"Connection refused:  {str(e)}\n")
            sys.exit(1)

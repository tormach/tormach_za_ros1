import subprocess
from .ecat_types import EtherCATTypes
from .logging import Logging


class EtherCATException(RuntimeError):
    pass


class EtherCATCommandArgsError(ValueError):
    pass


class EtherCATCommand:
    _command_registry = dict()
    _command_instances = dict()
    logger = Logging.getLogger(__name__)
    log_op = 'debug'
    parse_ethercat_output = False

    def __init_subclass__(cls, /, **kwargs):
        cls._command_registry[cls.command] = cls

    @classmethod
    def _get_command_instance(cls, command):
        return cls._command_instances.setdefault(
            command, cls._command_registry[command]()
        )

    command = None

    # Global options; see `ethercat --help`
    # `bool` defaults indicate flag options
    global_option_defaults = dict(
        # Options with args
        master=None,
        # Flag options (no args)
        force=False,
        quiet=False,
        verbose=False,
    )

    # Command options arnd arguments; see `ethercat {command} --help`
    command_option_defaults = dict()
    command_argument_specs = []

    def _resolve_options(self, kwargs, option_defaults):
        # Convert kwargs with keys in option_defaults into
        # command-line options; options with bool-type defaults are
        # flags (`--option`), either present or not; other options
        # have an arg (`--option=arg`)
        opts = list()
        for key, default in option_defaults.items():
            val = kwargs.pop(key, default)
            if isinstance(default, bool):  # --flag
                if val:
                    opts.append(f'--{key}')
            else:  # --opt=optarg
                if val is not None:
                    opts.append(f'--{key}={val}')
        return sorted(opts)

    def global_options(self, kwargs):
        return self._resolve_options(kwargs, self.global_option_defaults)

    def command_options(self, kwargs):
        return self._resolve_options(kwargs, self.command_option_defaults)

    def _resolve_command_arguments(self, args, argument_specs):
        # Check for too many args
        if len(args) > len(argument_specs):
            raise EtherCATCommandArgsError(
                f"Command {self.command} accepts "
                f"max {len(argument_specs)} arguments"
            )

        # Sort out which optional command arguments were omitted, and
        # check for too few args
        arg_specs = list(argument_specs)
        # Working backwards, remove optional arg specs until the
        # length of supplied args matches arg specs
        for i in range(len(argument_specs), 0, -1):
            if len(args) < len(arg_specs):
                if arg_specs[i - 1].get('optional', False):
                    arg_specs.pop(i - 1)
            if len(args) == len(arg_specs):
                break
        else:
            if len(argument_specs) > 0:
                raise EtherCATCommandArgsError(
                    f"Command {self.command} requires min. {len(arg_specs)} args"
                )

        # Process args into list and return them
        processed_args = list()
        for i, spec in enumerate(arg_specs):
            conv = spec.get('conv', lambda x: str(x))
            processed_args.append(conv(args[i]))
        return processed_args

    def command_arguments(self, args):
        return self._resolve_command_arguments(
            args, self.command_argument_specs
        )

    def run_args(self, *args, **kwargs):
        # Build command line
        run_args = [
            'ethercat',
            self.command,
            *self.global_options(kwargs),
            *self.command_options(kwargs),
            *self.command_arguments(args),
        ]
        # All kwargs should be used up
        if len(kwargs) != 0:
            raise EtherCATCommandArgsError(
                f"Unknown args '{', '.join(kwargs.keys())}' "
                f"to command {self.command}"
            )
        return run_args

    def run(self, *args, **kwargs):
        dry_run = kwargs.pop('dry_run', False)
        run_args = self.run_args(*args, **kwargs)
        if dry_run:
            self.logger.info(f"      dry_run: {' '.join(run_args)}")
            return None
        try:
            getattr(self.logger, self.log_op)('      ' + ' '.join(run_args))
            resp = subprocess.check_output(run_args).rstrip()
        except subprocess.CalledProcessError as e:
            raise EtherCATException(str(e))
        # This ought to be a map, and probably integrated with type
        # handling in EtherCATXMLReader!
        ectype = kwargs.get('type', None)
        if ectype is None:
            return resp
        if self.parse_ethercat_output:
            return EtherCATTypes.get_igh_type(ectype)(resp)

    @classmethod
    def run_command(cls, command, *args, **kwargs):
        command_obj = cls._get_command_instance(command)
        return command_obj.run(*args, **kwargs)


class EtherCATUpload(EtherCATCommand):
    command = 'upload'
    parse_ethercat_output = True
    command_option_defaults = dict(
        type=None,
        alias=None,
        position=None,
    )
    command_argument_specs = [
        dict(name='index', conv=lambda x: f'0x{x:04X}'),
        dict(name='subindex', conv=lambda x: f'0x{x:02X}', optional=True),
    ]


class EtherCATDownload(EtherCATUpload):
    command = 'download'
    parse_ethercat_output = False
    command_argument_specs = [
        *EtherCATUpload.command_argument_specs,
        dict(name='value'),
    ]
    log_op = 'info'


class EtherCATMaster(EtherCATCommand):
    command = 'master'


class EtherCATSlaves(EtherCATCommand):
    command = 'slaves'
    command_option_defaults = dict(
        alias=None,
        position=None,
        verbose=False,
    )


class EtherCATDebug(EtherCATCommand):
    command = 'debug'
    command_argument_specs = [
        dict(name='level'),
    ]


class EtherCATVersion(EtherCATCommand):
    command = 'version'


class EtherCATXML(EtherCATCommand):
    command = 'xml'
    command_option_defaults = dict(
        alias=None,
        position=None,
    )

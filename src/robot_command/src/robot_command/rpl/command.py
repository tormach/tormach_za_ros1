from abc import abstractmethod, ABC
from collections import namedtuple

import rospy

ProgramPosition = namedtuple('ProgramPosition', 'linum filename')


class CommandType:
    SYNC_COMMAND = 0
    ASYNC_COMMAND = 1
    SCOPED_COMMAND = 2


class Command(ABC):
    name = 'command'
    type_ = CommandType.SYNC_COMMAND

    def __init__(self):
        super().__init__()
        self.interpreter = None

    @abstractmethod
    def execute(self):
        pass

    def __str__(self):
        return self.name


class AsyncCommand(ABC):
    name = 'command'
    type_ = CommandType.ASYNC_COMMAND

    def __init__(self):
        super().__init__()
        self.interpreter = None

    @abstractmethod
    def is_similar(self, other):
        return self == other

    @abstractmethod
    def execute(self, sequence=None, last=False):
        pass

    def __str__(self):
        return self.name


class ScopedCommand(Command):
    type_ = CommandType.SCOPED_COMMAND

    def __init__(self):
        super().__init__()

    def execute(self):
        pass  # does nothing for scope

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, type_, value, traceback):
        pass


class CombinedCommand:
    def __init__(self, commands):
        self.commands = commands

    def execute(self):
        data = []
        result = []
        for command in self.commands[:-1]:
            result.append(command.execute(data))
        result.append(self.commands[-1].execute(data, last=True))
        return result

    def __str__(self):
        return f'combined_command: {len(self.commands)} commands'


RegisteredCommand = namedtuple('RegisteredCommand', 'name command')


class CommandInterpreter:
    status_report_cb = None

    def __init__(self):
        self._async_enabled = True
        self._async_commands = []
        self._command_register = []

    @property
    def async_enabled(self):
        return self._async_enabled

    @async_enabled.setter
    def async_enabled(self, value):
        self._async_enabled = value

    def rpl_program_start(self):
        del self._async_commands[:]
        self._async_enabled = False

    def rpl_main_program_start(self):
        pass

    def rpl_main_program_end(self):
        self._execute_async_commands()

    def register_command(self, name, command, type_=CommandType.SYNC_COMMAND):
        if type_ == CommandType.ASYNC_COMMAND:
            rospy.logdebug(f'registering async command {name}')
            self._register_async_command(name, command)
        elif type_ == CommandType.SYNC_COMMAND:
            rospy.logdebug(f'registering sync command {name}')
            self._register_sync_command(name, command)
        else:
            rospy.logdebug(f'registering scoped command {name}')
            self._register_scoped_command(name, command)

    def register_commands(self, interpreter, commands=None):
        if commands is None:
            commands = []
        if interpreter == 'execution':
            from ..execution_commands import commands
        elif interpreter == 'simulation':
            from ..simulation_commands import commands
        for command in commands:
            self.register_command(
                name=command.name, command=command, type_=command.type_
            )

    def register_commands_to_namespace(self, namespace):
        for command in self._command_register:
            namespace[command.name] = command.command

    @staticmethod
    def init_commands(interpreter):
        init = None
        if interpreter == 'execution':
            from ..execution_commands import init
        elif interpreter == 'simulation':
            from ..simulation_commands import init
        if init:
            init()

    def report_current_command(self, command):
        if self.status_report_cb:
            self.status_report_cb(command)

    def _add_async_command(self, cmd):
        self._async_commands.append(cmd)

    def _check_async_is_similar(self, cmd):
        if len(self._async_commands) == 0:
            return True
        return cmd.is_similar(self._async_commands[-1])

    def _execute_async_commands(self):
        if len(self._async_commands) == 0:
            return
        cmd = CombinedCommand(self._async_commands)
        result = cmd.execute()
        del self._async_commands[:]
        return result

    def _register_async_command(self, name, command):
        def run_command(*args, **kwargs):
            cmd = command(*args, **kwargs)
            cmd.interpreter = self
            if not self._check_async_is_similar(cmd):
                return self._execute_async_commands()
            if self._async_enabled:
                self._add_async_command(cmd)
            else:
                return cmd.execute()

        self._command_register.append(
            RegisteredCommand(name=name, command=run_command)
        )
        return run_command

    def _register_sync_command(self, name, command):
        def run_command(*args, **kwargs):
            self._execute_async_commands()
            cmd = command(*args, **kwargs)
            cmd.interpreter = self
            return cmd.execute()

        self._command_register.append(
            RegisteredCommand(name=name, command=run_command)
        )
        return run_command

    def _register_scoped_command(self, name, command):
        interpreter = self

        class ScopeClass(command):
            def __init__(self, *args, **kwargs):
                interpreter._execute_async_commands()
                super().__init__(*args, **kwargs)
                self.interpreter = interpreter

            def __exit__(self, exc_type, exc_val, exc_tb):
                interpreter._execute_async_commands()
                super().__exit__(exc_type, exc_val, exc_tb)

        self._command_register.append(
            RegisteredCommand(name=name, command=ScopeClass)
        )
        return ScopeClass

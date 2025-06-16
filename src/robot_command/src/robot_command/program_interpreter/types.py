from collections import namedtuple
from enum import Enum, auto


class InterpreterCommand(Enum):
    Start = auto()
    Stop = auto()
    Pause = auto()
    PauseActive = auto()
    Continue = auto()
    Update = auto()
    Load = auto()
    LoadError = auto()
    Unload = auto()
    MDI = auto()
    Step = auto()
    ReloadCheck = auto()


class InterpreterState(Enum):
    Idle = auto()
    Stopped = auto()
    Running = auto()
    Paused = auto()
    PausedActive = auto()
    RuntimeError = auto()
    LoadError = auto()
    Initialized = auto()


class InterpreterContext(Enum):
    Undefined = auto()
    Program = auto()
    MDI = auto()


class InterpreterError(Exception):
    pass


class ProgramNotLoadedError(InterpreterError):
    pass


class ProgramNotRunningError(InterpreterError):
    pass


class ProgramAlreadyRunningError(InterpreterError):
    pass


class ProgramSyntaxError(SyntaxError):
    pass


class ProgramWrongStateError(InterpreterError):
    pass


class ProgramFileIOError(IOError):
    pass


class MdiSyntaxError(SyntaxError):
    pass


ProgramState = namedtuple('ProgramState', 'state context')
ProgramCommand = namedtuple('ProgramCommand', 'command data')
ProgramPosition = namedtuple('ProgramPosition', 'line_number, filename')
ProgramError = namedtuple('ProgramError', 'type message')
ProgramTree = namedtuple('ProgramTree', 'tree path')
ProgramInterrupt = namedtuple('ProgramInterrupt', 'source_id number value')
FSMState = namedtuple('FSMState', 'event source destination')
InterpreterReloadRequired = namedtuple('InterpreterReloadRequired', 'required')
